"""
Module with routines to handle Python and Flyable list
"""

from flyable.parse.parser_visitor import ParserVisitor
import flyable.code_gen.exception as excp
import flyable.code_gen.code_gen as gen
import flyable.code_gen.code_type as code_type
import flyable.code_gen.runtime as runtime
import flyable.code_gen.ref_counter as ref_counter
import flyable.data.type_hint as hint
import flyable.data.lang_type as lang_type
import flyable.code_gen.debug as debug


def instanciate_python_list(code_gen, builder, len):
    """
    Generate the code to allocate a Python List
    """
    new_list_args_types = [code_type.get_int64()]
    new_list_func = code_gen.get_or_create_func("PyList_New", code_type.get_py_obj_ptr(code_gen),
                                                new_list_args_types, gen.Linkage.EXTERNAL)
    return builder.call(new_list_func, [len])


def python_list_set(visitor, list, index, item):
    """
    Generate the code to set an element in a Python List
    """
    builder, code_gen = visitor.get_builder(), visitor.get_code_gen()
    set_item_args_types = [code_type.get_py_obj_ptr(code_gen), code_type.get_int64(),
                           code_type.get_py_obj_ptr(code_gen)]
    set_item_func = code_gen.get_or_create_func("PyList_SetItem", code_type.get_int32(),
                                                set_item_args_types, gen.Linkage.EXTERNAL)
    result = builder.call(set_item_func, [list, index, item])
    return result


def python_list_append(visitor, list, item_type, item):
    """
    Generate the code to set an element in a Python List
    """

    builder, code_gen = visitor.get_builder(), visitor.get_code_gen()

    item_type, item = runtime.value_to_pyobj(code_gen, builder, item, item_type)

    if not hint.is_incremented_type(item_type):
        ref_counter.ref_incr(visitor.get_builder(), item_type, item)

    new_alloca_block = builder.create_block()
    continue_block = builder.create_block()

    list = visitor.get_builder().ptr_cast(list, code_type.get_list_obj_ptr(visitor.get_code_gen()))
    capacity = python_list_capacity_ptr(visitor, list)
    capacity = visitor.get_builder().load(capacity)

    size_ptr = python_list_len_ptr(visitor, list)
    size = builder.load(size_ptr)
    new_size = builder.add(size, builder.const_int64(1))

    need_new_alloca = builder.eq(capacity, size)
    builder.cond_br(need_new_alloca, new_alloca_block, continue_block)

    builder.set_insert_block(new_alloca_block)
    resize_args_types = [code_type.get_list_obj_ptr(code_gen), code_type.get_int64()]
    resize_func = code_gen.get_or_create_func("python_list_resize", code_type.get_int32(), resize_args_types,
                                              gen.Linkage.EXTERNAL)

    builder.call(resize_func, [list, new_size])
    builder.br(continue_block)

    builder.set_insert_block(continue_block)
    content = builder.load(python_list_get_content_ptr(visitor, list))
    content = builder.ptr_cast(content, code_type.get_py_obj_ptr(code_gen).get_ptr_to())
    item_ptr = builder.gep2(content, code_type.get_py_obj_ptr(code_gen), [size])
    builder.store(item, item_ptr)  # Set the item in the buffer
    builder.store(new_size, size_ptr)  # Set the new size in case it didn't enter the resize


def python_list_capacity_ptr(visitor, list):
    builder, code_gen = visitor.get_builder(), visitor.get_code_gen()
    list = builder.ptr_cast(list, code_type.get_list_obj_ptr(code_gen))
    return builder.gep(list, builder.const_int32(0), builder.const_int32(4))


def python_list_get_content_ptr(visitor, list):
    list = visitor.get_builder().ptr_cast(list, code_type.get_list_obj_ptr(visitor.get_code_gen()))
    return visitor.get_builder().gep(list, visitor.get_builder().const_int32(0), visitor.get_builder().const_int32(3))


def python_list_array_get_item(visitor, list_type, list, index):
    builder, code_gen = visitor.get_builder(), visitor.get_code_gen()
    valid_index_block = builder.create_block()
    wrong_index_block = builder.create_block()
    size = python_list_len(visitor, list)
    real_index = visitor.get_builder().mod(index, size)
    valid_bounds = visitor.get_builder().lt(real_index, size)
    builder.cond_br(valid_bounds, valid_index_block, wrong_index_block)
    builder.set_insert_block(valid_index_block)
    content = python_list_get_content_ptr(visitor, list)
    content = builder.load(content)
    content = builder.ptr_cast(content, list_type.get_content().to_code_type(visitor.get_code_gen()).get_ptr_to())
    content = builder.gep2(content, list_type.get_content().to_code_type(visitor.get_code_gen()), [index])
    result = builder.load(content)

    builder.set_insert_block(wrong_index_block)
    excp.raise_index_error(visitor)
    excp.handle_raised_excp(visitor)

    builder.set_insert_block(valid_index_block)
    return result


def python_list_array_get_item_unsafe(visitor: ParserVisitor, list_type: lang_type.LangType, list, index: int):
    builder, code_gen = visitor.get_builder(), visitor.get_code_gen()
    content = python_list_get_content_ptr(visitor, list)
    content = builder.load(content)
    content = builder.ptr_cast(content, list_type.get_content().to_code_type(visitor.get_code_gen()).get_ptr_to())
    content = builder.gep2(content, list_type.get_content().to_code_type(visitor.get_code_gen()), [index])
    result = builder.load(content)
    return result


def python_list_len_ptr(visitor: ParserVisitor, list):
    list = visitor.get_builder().ptr_cast(list, code_type.get_list_obj_ptr(visitor.get_code_gen()))
    return visitor.get_builder().gep(list, visitor.get_builder().const_int32(0), visitor.get_builder().const_int32(2))


def python_list_len(visitor, list):
    """
    Generate the code that returns the len of the list
    """
    return visitor.get_builder().load(python_list_len_ptr(visitor, list))

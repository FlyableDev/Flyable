"""
Module for Python tuple related functions
"""

from flyable.code_gen.code_type import CodeType
import flyable.code_gen.code_gen as gen
import flyable.code_gen.code_type as code_type
import flyable.code_gen.list as list_gen
import flyable.code_gen.ref_counter as ref_counter
import flyable.data.lang_type as lang_type
import flyable.code_gen.fly_obj as fly_obj


def python_tuple_new(code_gen, builder, size):
    """
    Generate the code to allocate a Python Tuple
    """
    new_list_args_types = [code_type.get_int64()]
    new_list_func = code_gen.get_or_create_func("PyTuple_New", code_type.get_py_obj_ptr(code_gen),
                                                new_list_args_types, gen.Linkage.EXTERNAL)
    return builder.call(new_list_func, [size])


def python_tuple_new_alloca(visitor, size):
    """
    Generate the code to allocate a Python Tuple on the stack. Much faster then an allocation on the heap.
    """
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()
    current_block = builder.get_current_block()
    builder.set_insert_block(visitor.get_entry_block())
    tuple_result = builder.alloca(code_type.get_array_of(code_type.get_py_obj_ptr(code_gen), size + 10))

    type_ptr = fly_obj.get_py_obj_type_ptr(builder, tuple_result)
    type_ptr = builder.ptr_cast(type_ptr, code_type.get_py_obj_ptr(code_gen).get_ptr_to())
    builder.store(builder.load(builder.global_var(code_gen.get_tuple_type())), type_ptr)

    tuple_result = builder.ptr_cast(tuple_result, code_gen.get_py_tuple_struct().to_code_type().get_ptr_to())

    ref_counter.set_ref_count(visitor, tuple_result, builder.const_int64(5))
    builder.store(builder.const_int64(size), python_tuple_get_size_ptr(visitor, tuple_result))

    tuple_result = builder.ptr_cast(tuple_result, code_type.get_py_obj_ptr(code_gen))

    builder.set_insert_block(current_block)

    return tuple_result


def python_tuple_set(code_gen, builder, list, index, item):
    """
    Generate the code to set an element in a Python Tuple
    """
    set_item_args_types = [code_type.get_py_obj_ptr(code_gen), code_type.get_int64(),
                           code_type.get_py_obj_ptr(code_gen)]
    set_item_func = code_gen.get_or_create_func("PyTuple_SetItem", code_type.get_int32(),
                                                set_item_args_types, gen.Linkage.EXTERNAL)
    return builder.call(set_item_func, [list, index, item])


def python_tuple_set_unsafe(visitor, tuple, index, item):
    """
    Generate the code to set an element in a Python Tuple.
    Should only be used for filling new tuples.
    """
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()
    tuple = builder.ptr_cast(tuple, code_gen.get_py_tuple_struct().to_code_type().get_ptr_to())
    content_type = code_type.get_array_of(code_type.get_py_obj_ptr(code_gen), index + 1).get_ptr_to()
    content = builder.ptr_cast(python_tuple_get_content_ptr(visitor, tuple), content_type)
    content = builder.gep(content, builder.const_int32(0), builder.const_int32(index))
    builder.store(item, content)


def python_tuple_get_content_ptr(visitor, tuple):
    builder = visitor.get_builder()
    return builder.gep(tuple, builder.const_int32(0), builder.const_int32(3))


def python_tuple_get_size_ptr(visitor, tuple):
    builder = visitor.get_builder()
    return builder.gep(tuple, builder.const_int32(0), builder.const_int32(2))

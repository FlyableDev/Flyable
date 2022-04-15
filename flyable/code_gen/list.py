"""
Module with routines to handle Python and Flyable list
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flyable.code_gen.code_builder import CodeBuilder
    from flyable.code_gen.code_gen import CodeGen
    from flyable.parse.parser_visitor import ParserVisitor

import flyable.code_gen.exception as excp
import flyable.code_gen.code_gen as gen
import flyable.code_gen.code_type as code_type
import flyable.code_gen.runtime as runtime
import flyable.code_gen.ref_counter as ref_counter
import flyable.data.type_hint as hint
import flyable.data.lang_type as lang_type


def instanciate_python_list(code_gen: CodeGen, builder: CodeBuilder, len: int):
    """
    Generate the code to allocate a Python List
    """
    new_list_args_types = [code_type.get_int64()]
    new_list_func = code_gen.get_or_create_func("PyList_New", code_type.get_py_obj_ptr(code_gen),
                                                new_list_args_types, gen.Linkage.EXTERNAL)
    return builder.call(new_list_func, [len])


def python_list_set(visitor: ParserVisitor, list: int, index: int, item):
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


def python_list_append(visitor: ParserVisitor, list: int, item_type: lang_type.LangType, item: int):
    builder, code_gen = visitor.get_builder(), visitor.get_code_gen()
    item_type, item = runtime.value_to_pyobj(visitor, item, item_type)
    args_types = [code_type.get_py_obj_ptr(code_gen), code_type.get_py_obj_ptr(code_gen)]
    func = code_gen.get_or_create_func("PyList_Append", code_type.get_py_obj_ptr(code_gen),
                                                args_types, gen.Linkage.EXTERNAL)
    builder.call(func, [list, item])

"""
The following commented function calls python_list_resize which is not an external cpython symbole
"""

# def python_list_append(visitor: ParserVisitor, list: int, item_type: lang_type.LangType, item: int):
#     """
#     Generate the code to set an element in a Python List
#     """
#
#     builder, code_gen = visitor.get_builder(), visitor.get_code_gen()
#
#     item_type, item = runtime.value_to_pyobj(code_gen, builder, item, item_type)
#
#     if not hint.is_incremented_type(item_type):
#         ref_counter.ref_incr(visitor.get_builder(), item_type, item)
#
#     new_alloca_block = builder.create_block("List New Allocation")
#     continue_block = builder.create_block("After List")
#
#     list = builder.ptr_cast(list, code_type.get_list_obj_ptr(visitor.get_code_gen()))
#     capacity = python_list_capacity_ptr(visitor, list)
#     capacity = builder.load(capacity)
#
#     size_ptr = python_list_len_ptr(visitor, list)
#     size = builder.load(size_ptr)
#     new_size = builder.add(size, builder.const_int64(1))
#
#     need_new_alloca = builder.eq(capacity, size)
#     builder.cond_br(need_new_alloca, new_alloca_block, continue_block)
#
#     builder.set_insert_block(new_alloca_block)
#     resize_args_types = [code_type.get_list_obj_ptr(code_gen), code_type.get_int64()]
#     resize_func = code_gen.get_or_create_func("python_list_resize", code_type.get_int32(), resize_args_types,
#                                               gen.Linkage.EXTERNAL)
#
#     builder.call(resize_func, [list, new_size])
#     builder.br(continue_block)
#
#     builder.set_insert_block(continue_block)
#     content = builder.load(python_list_get_content_ptr(visitor, list))
#     content = builder.ptr_cast(content, code_type.get_py_obj_ptr(code_gen).get_ptr_to())
#     item_ptr = builder.gep2(content, code_type.get_py_obj_ptr(code_gen), [size])
#     builder.store(item, item_ptr)  # Set the item in the buffer
#     builder.store(new_size, size_ptr)  # Set the new size in case it didn't enter the resize


def python_list_capacity_ptr(visitor: ParserVisitor, list: int):
    builder, code_gen = visitor.get_builder(), visitor.get_code_gen()
    list = builder.ptr_cast(list, code_type.get_list_obj_ptr(code_gen))
    return builder.gep(list, builder.const_int32(0), builder.const_int32(4))


def python_list_get_content_ptr(visitor: ParserVisitor, list: int):
    list = visitor.get_builder().ptr_cast(list, code_type.get_list_obj_ptr(visitor.get_code_gen()))
    return visitor.get_builder().gep(list, visitor.get_builder().const_int32(0), visitor.get_builder().const_int32(3))


def python_list_array_get_item(visitor: ParserVisitor, list_type: lang_type.LangType, list: int, index: int):
    builder, code_gen = visitor.get_builder(), visitor.get_code_gen()
    valid_index_block = builder.create_block("List Valid Index")
    wrong_index_block = builder.create_block("List Wrong Index")
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


def python_list_array_get_item_unsafe(visitor: ParserVisitor, list_type: lang_type.LangType, list: int, index: int):
    ptr = python_list_array_get_item_ptr_unsafe(visitor, list_type, list, index)
    result = visitor.get_builder().load(ptr)
    return result


def python_list_array_get_item_ptr_unsafe(visitor: ParserVisitor, list_type: lang_type.LangType, list: int, index: int):
    builder = visitor.get_builder()
    content = python_list_get_content_ptr(visitor, list)
    content = builder.load(content)
    content = builder.ptr_cast(content, list_type.get_content().to_code_type(visitor.get_code_gen()).get_ptr_to())
    content = builder.gep2(content, list_type.get_content().to_code_type(visitor.get_code_gen()), [index])
    return content


def python_list_len_ptr(visitor: ParserVisitor, list: int):
    list = visitor.get_builder().ptr_cast(list, code_type.get_list_obj_ptr(visitor.get_code_gen()))
    return visitor.get_builder().gep(list, visitor.get_builder().const_int32(0), visitor.get_builder().const_int32(2))


def python_list_len(visitor: ParserVisitor, list: int):
    """
    Generate the code that returns the len of the list
    """
    return visitor.get_builder().load(python_list_len_ptr(visitor, list))

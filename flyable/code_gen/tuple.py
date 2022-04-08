"""
Module for Python tuple related functions
"""
from __future__ import annotations
from typing import TYPE_CHECKING
import flyable.code_gen.code_gen as gen
import flyable.code_gen.code_type as code_type
import flyable.code_gen.ref_counter as ref_counter
import flyable.code_gen.fly_obj as fly_obj
from flyable.data import lang_type
from flyable.parse.parser_visitor import ParserVisitor
import flyable.code_gen.exception as excp

if TYPE_CHECKING:
    from flyable.code_gen.code_builder import CodeBuilder


def python_tuple_new(code_gen: gen.CodeGen, builder: CodeBuilder, size: int):
    """
    Generate the code to allocate a Python Tuple
    """
    new_list_args_types = [code_type.get_int64()]
    new_list_func = code_gen.get_or_create_func("PyTuple_New", code_type.get_py_obj_ptr(code_gen),
                                                new_list_args_types, gen.Linkage.EXTERNAL)
    return builder.call(new_list_func, [size])


def python_tuple_new_alloca(visitor: ParserVisitor, size: int):
    """
    Generate the code to allocate a Python Tuple on the stack. Much faster then an allocation on the heap.
    """
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    tuple_result = visitor.generate_entry_block_var(
        code_type.get_array_of(code_type.get_py_obj_ptr(code_gen), size + 10))

    tuple_result = builder.ptr_cast(tuple_result, code_gen.get_py_tuple_struct().to_code_type().get_ptr_to())

    type_ptr = fly_obj.get_py_obj_type_ptr(builder, tuple_result)
    type_ptr = builder.ptr_cast(type_ptr, code_type.get_py_obj_ptr(code_gen).get_ptr_to())
    builder.store(builder.global_var(code_gen.get_tuple_type()), type_ptr)

    ref_counter.set_ref_count(builder, tuple_result, builder.const_int64(5))
    builder.store(builder.const_int64(size), python_tuple_get_size_ptr(visitor, tuple_result))

    tuple_result = builder.ptr_cast(tuple_result, code_type.get_py_obj_ptr(code_gen))

    return tuple_result


def python_tuple_set(code_gen: gen.CodeGen, builder: CodeBuilder, list: int, index: int, item: int):
    """
    Generate the code to set an element in a Python Tuple
    """
    set_item_args_types = [code_type.get_py_obj_ptr(code_gen), code_type.get_int64(),
                           code_type.get_py_obj_ptr(code_gen)]
    set_item_func = code_gen.get_or_create_func("PyTuple_SetItem", code_type.get_int32(),
                                                set_item_args_types, gen.Linkage.EXTERNAL)
    return builder.call(set_item_func, [list, index, item])


def python_tuple_set_unsafe(visitor: ParserVisitor, tuple: int, index: int, item: int):
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


def python_tuple_get_content_ptr(visitor: ParserVisitor, tuple: int):
    builder = visitor.get_builder()
    tuple = builder.ptr_cast(tuple, code_type.get_tuple_obj_ptr(visitor.get_code_gen()))
    return builder.gep(tuple, builder.const_int32(0), builder.const_int32(3))


def python_tuple_get_item(visitor: ParserVisitor, tuple_type: lang_type.LangType, tuple: int, index: int):
    builder, code_gen = visitor.get_builder(), visitor.get_code_gen()
    valid_index_block = builder.create_block("Tuple Valid Index")
    wrong_index_block = builder.create_block("Tuple Wrong Index")
    size = builder.load(python_tuple_get_size_ptr(visitor, tuple))
    real_index = builder.mod(index, size)
    valid_bounds = builder.lt(real_index, size)
    builder.cond_br(valid_bounds, valid_index_block, wrong_index_block)
    builder.set_insert_block(valid_index_block)
    content = builder.ptr_cast(tuple, code_type.get_py_obj_ptr(code_gen).get_ptr_to())

    # + 3 to skip the ref count, type and counts
    content = builder.gep2(content, code_type.get_py_obj_ptr(code_gen), [index + 3])
    result = builder.load(content)

    builder.set_insert_block(wrong_index_block)
    excp.raise_index_error(visitor)
    excp.handle_raised_excp(visitor)

    builder.set_insert_block(valid_index_block)
    return result


def python_tuple_get_unsafe_item_ptr(visitor: ParserVisitor, tuple_type: lang_type.LangType, tuple: int, index: int):
    builder, code_gen = visitor.get_builder(), visitor.get_code_gen()
    content = builder.ptr_cast(tuple, code_type.get_py_obj_ptr(code_gen).get_ptr_to())

    # + 3 to skip the ref count, type and counts
    gep_index = builder.add(index, builder.const_int64(3))
    content = builder.gep2(content, code_type.get_py_obj_ptr(code_gen), [gep_index])
    return content


def python_tuple_get_size_ptr(visitor: ParserVisitor, tuple: int):
    builder = visitor.get_builder()
    tuple = builder.ptr_cast(tuple, code_type.get_tuple_obj_ptr(visitor.get_code_gen()))
    return builder.gep(tuple, builder.const_int32(0), builder.const_int32(2))

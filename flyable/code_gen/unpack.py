from __future__ import annotations
from typing import TYPE_CHECKING

from flyable.data import lang_type

if TYPE_CHECKING:
    from flyable.parse.parser_visitor import ParserVisitor

import ast
import flyable.code_gen.caller as caller
from flyable.data.lang_type import *
import flyable.data.type_hint as hint
import flyable.code_gen.list as gen_list
import flyable.code_gen.dict as gen_dict
import flyable.code_gen.exception as excp
import flyable.code_gen.ref_counter as ref_counter
import flyable.parse.exception.unsupported as unsupported
import flyable.code_gen.code_gen as gen
import flyable.code_gen.debug as debug

def unpack_assignation(visitor: ParserVisitor, targets, value_type, value, node):
    for target in targets:
        if isinstance(target, ast.Starred):
            raise unsupported.FlyableUnsupported()
    if value_type.is_list() or value_type.is_tuple():
        unpack_list_or_tuple_assignation(visitor, targets, value_type, value, node)
    elif value_type.is_dict():
        value = gen_dict.python_dict_get_keys(visitor, value)
        value_type = lang_type.get_list_of_python_obj_type()
        unpack_list_or_tuple_assignation(visitor, targets, value_type, value, node)
    else:
        unpack_iterable_assignation(visitor, targets, value_type, value, node)

def unpack_list_or_tuple_assignation(visitor: ParserVisitor, targets, value_type, value, node):
    builder = visitor.get_builder()
    unpack_block = builder.create_block("Unpack")
    error_block = builder.create_block("Unpack Error")
    continue_block = builder.create_block("After Unpack")

    len_targets = builder.const_int64(len(targets))
    len_value = gen_list.python_list_len(visitor, value)

    test = builder.eq(len_value, len_targets)
    builder.cond_br(test, unpack_block, error_block)
    builder.set_insert_block(unpack_block)

    for i, target in enumerate(targets):
        index_type = get_int_type()
        index_type.add_hint(hint.TypeHintConstInt(i))
        index_value = builder.const_int64(i)
        args_types = [index_type]
        args = [index_value]
        value_type_i, value_i = caller.call_obj(visitor, "__getitem__", value, value_type, args, args_types, {})
        if not hint.is_incremented_type(value_type_i):
            ref_counter.ref_incr(builder, value_type_i, value_i)
        do_assignation(visitor, target, value_type_i, value_i, node)
        ref_counter.ref_decr(visitor, value_type_i, value_i)

    builder.br(continue_block)

    builder.set_insert_block(error_block)
    excp.raise_index_error(visitor)     # value doesn't have as many elements as targets

    builder.set_insert_block(continue_block)
    ref_counter.ref_decr(visitor, value_type, value)

def unpack_iterable_assignation(visitor: ParserVisitor, targets, value_type, value, node):
    builder, code_gen = visitor.get_builder(), visitor.get_code_gen()
    error_block = builder.create_block("Unpack Error")
    continue_block = builder.create_block("After Unpack")

    iterable_type, iterator = caller.call_obj(visitor, "__iter__", value, value_type, [], [], {})

    for i, target in enumerate(targets):
        test_next = builder.create_block("Test Next")
        builder.br(test_next)
        builder.set_insert_block(test_next)

        next_type, next_value = caller.call_obj(visitor, "__next__", iterator, iterable_type, [], [], {})

        null_ptr = builder.const_null(code_type.get_py_obj_ptr(code_gen))
        excp.py_runtime_clear_error(code_gen, builder)
        test = builder.eq(next_value, null_ptr)
        unpack_block = builder.create_block("Unpack")
        builder.cond_br(test, error_block, unpack_block)

        builder.set_insert_block(unpack_block)
        do_assignation(visitor, target, next_type, next_value, node)

        if i == len(targets) - 1:
            next_type, next_value = caller.call_obj(visitor, "__next__", iterator, iterable_type, [], [], {})
            null_ptr = builder.const_null(code_type.get_py_obj_ptr(code_gen))
            excp.py_runtime_clear_error(code_gen, builder)
            test = builder.eq(next_value, null_ptr)
            builder.cond_br(test, continue_block, error_block)

    builder.set_insert_block(error_block)
    excp.raise_index_error(visitor)     # iterable returns more or less values then there are elements in targets

    builder.set_insert_block(continue_block)
    ref_counter.ref_decr(visitor, value_type, value)


def do_assignation(visitor: ParserVisitor, target, value_type, value, node):
    if isinstance(target, ast.Tuple) or isinstance(target, ast.List):
        new_targets = []
        for t in target.elts:
            new_targets.append(t)
        unpack_assignation(visitor, new_targets, value_type, value, node)
    elif isinstance(target, ast.Name) or isinstance(target, ast.Subscript):
        visitor.set_assign_type(value_type)
        visitor.set_assign_value(value)
        visitor.visit_node(target)
    else:
        visitor.get_parser().throw_error("Incorrect target type encountered when unpacking ", node.lineno,
                                         node.end_col_offset)
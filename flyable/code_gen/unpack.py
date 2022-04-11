from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flyable.parse.parser_visitor import ParserVisitor

import flyable.code_gen.caller as caller
from flyable.data.lang_type import *
import flyable.data.type_hint as hint
import flyable.code_gen.list as gen_list
import flyable.code_gen.tuple as gen_tuple
import flyable.code_gen.exception as excp
import flyable.code_gen.ref_counter as ref_counter

def unpack_list_or_tuple(visitor: ParserVisitor, seq_type, seq, instr):
    builder = visitor.get_builder()
    size = instr.arg
    unpack_block = builder.create_block("Unpack")
    # error_block = builder.create_block("Unpack Error")
    continue_block = builder.create_block("After Unpack")

    # size_value = builder.const_int64(size)
    # len_value = None
    if seq_type.is_tuple():
        len_value = gen_tuple.python_tuple_len(visitor, seq)
    elif seq_type.is_list():
        len_value = gen_list.python_list_len(visitor, seq)

    # test = builder.eq(len_value, size_value)
    # builder.cond_br(test, unpack_block, error_block)
    builder.set_insert_block(unpack_block)

    for i in reversed(range(size)):
        index_type = get_int_type()
        index_type.add_hint(hint.TypeHintConstInt(i))
        index_value = builder.const_int64(i)
        args_types = [index_type]
        args = [index_value]
        value_type_i, value_i = caller.call_obj(visitor, "__getitem__", seq, seq_type, args, args_types, {})
        if not hint.is_incremented_type(value_type_i):
            ref_counter.ref_incr(builder, value_type_i, value_i)
        visitor.push(value_type_i, value_i)

    builder.br(continue_block)

    # builder.set_insert_block(error_block)
    # visitor.visit_unpack_sequence(instr)

    builder.set_insert_block(continue_block)

def unpack_iterable(visitor: ParserVisitor, seq_type, seq, size):
    builder, code_gen = visitor.get_builder(), visitor.get_code_gen()
    # not_enough_values_error_block = builder.create_block("Not Enough Values Unpack Error")
    # too_many_values_error_block = builder.create_block("Too Many Values Unpack Error")
    # not_an_iterator_error_block = builder.create_block("Not An Iterator Error")
    unpack_block = builder.create_block("Unpack")
    continue_block = builder.create_block("After Unpack")
    test_next = builder.create_block("Test Next")

    iterable_type, iterator = caller.call_obj(visitor, "__iter__", seq, seq_type, [], [], {})
    # null_ptr = builder.const_null(code_type.get_py_obj_ptr(code_gen))
    # test = builder.eq(iterator, null_ptr)
    # builder.cond_br(test, not_an_iterator_error_block, unpack_block)

    builder.br(unpack_block)
    builder.set_insert_block(unpack_block)

    temp_stack = []

    for i in range(size):
        builder.br(test_next)
        builder.set_insert_block(test_next)

        next_type, next_value = caller.call_obj(visitor, "__next__", iterator, iterable_type, [], [], {})
        temp_stack.append((next_type, next_value))

        # excp.py_runtime_clear_error(code_gen, builder)
        # test = builder.eq(next_value, null_ptr)
        # test_next = builder.create_block("Test Next")
        # builder.cond_br(test, not_enough_values_error_block, test_next)
        if i != size - 1:
            test_next = builder.create_block("Test Next")
            builder.br(test_next)

        if i == size - 1:
            # builder.set_insert_block(test_next)
            # next_type, next_value = caller.call_obj(visitor, "__next__", iterator, iterable_type, [], [], {})
            # excp.py_runtime_clear_error(code_gen, builder)
            # test = builder.eq(next_value, null_ptr)
            # builder.cond_br(test, continue_block, too_many_values_error_block)
            builder.br(continue_block)  # to replace with a condbr when we will have a better support for exception

    # builder.set_insert_block(not_an_iterator_error_block)
    # # "cannot unpack non_iterable object"
    # excp.raise_index_error(visitor) #TODO: give more info when raising the error
    #
    # builder.set_insert_block(not_enough_values_error_block)
    # # "not enough values to unpack (expected " + size + ", got " + i+1 + ")"
    # excp.raise_index_error(visitor) #TODO: give more info when raising the error
    #
    # builder.set_insert_block(too_many_values_error_block)
    # # "too many values to unpack (expected " + size + ")"
    # excp.raise_index_error(visitor) #TODO: give more info when raising the error

    builder.set_insert_block(continue_block)
    for i in range(size):
        type, value = temp_stack.pop(-1)
        visitor.push(type, value)

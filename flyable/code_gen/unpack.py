from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flyable.parse.parser_visitor import ParserVisitor

import flyable.code_gen.caller as caller
from flyable.data.lang_type import *
import flyable.data.type_hint as hint
import flyable.code_gen.list as gen_list
import flyable.code_gen.tuple as gen_tuple
import flyable.code_gen.slice as gen_slice
import flyable.code_gen.exception as excp
import flyable.code_gen.ref_counter as ref_counter
import flyable.code_gen.runtime as runtime

def unpack_list_or_tuple(visitor: ParserVisitor, seq_type, seq, instr):
    builder = visitor.get_builder()
    arg_count = instr.arg
    unpack_block = builder.create_block("Unpack")
    # error_block = builder.create_block("Unpack Error")
    continue_block = builder.create_block("After Unpack")

    # arg_count = builder.const_int64(arg_count)
    # len_value = None
    if seq_type.is_tuple():
        len_value = gen_tuple.python_tuple_len(visitor, seq)
    elif seq_type.is_list():
        len_value = gen_list.python_list_len(visitor, seq)

    # test = builder.eq(len_value, arg_count)
    # builder.cond_br(test, unpack_block, error_block)
    builder.set_insert_block(unpack_block)

    for i in reversed(range(arg_count)):
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

def unpack_iterable(visitor: ParserVisitor, seq_type, seq, arg_count, arg_count_after):
    builder, code_gen = visitor.get_builder(), visitor.get_code_gen()
    # not_an_iterator_error_block = builder.create_block("Not An Iterator Error")
    continue_block = builder.create_block("After Unpack")

    iterable_type, iterator = caller.call_obj(visitor, "__iter__", seq, seq_type, [], [], {})
    # null_ptr = builder.const_null(code_type.get_py_obj_ptr(code_gen))
    # test = builder.eq(iterator, null_ptr)
    # builder.cond_br(test, not_an_iterator_error_block, unpack_block)

    temp_stack = []

    if arg_count > 0:
        unpack_first_args(arg_count, arg_count_after, continue_block, iterable_type, iterator, temp_stack, visitor)

    # builder.set_insert_block(not_an_iterator_error_block)
    # # "cannot unpack non_iterable object"
    # excp.raise_index_error(visitor) #TODO: give more info when raising the error

    if arg_count_after != -1:
        args_after = builder.create_block("Args After")
        array_type, array = unpack_rest_of_iterator_to_list(args_after, iterable_type, iterator, visitor)

        builder.set_insert_block(args_after)
        array_length = gen_list.python_list_len(visitor, array)
        sub_list_type, sub_list_value = get_sub_list(arg_count_after, array, array_type, array_length, visitor)
        temp_stack.append((sub_list_type, sub_list_value))

        for j in reversed(range(1, arg_count_after + 1)):
            index_to_subtract = builder.const_int64(j)
            index_value = builder.sub(array_length, index_to_subtract)
            arg_after_type, arg_after_value = caller.call_obj(visitor, "__getitem__", array, array_type, [index_value], [get_int_type()], {})
            temp_stack.append((arg_after_type, arg_after_value))

        ref_counter.ref_decr(visitor, array_type, array)
        builder.br(continue_block)

    builder.set_insert_block(continue_block)
    for k in range(len(temp_stack)):
        type, value = temp_stack.pop()
        visitor.push(type, value)


def unpack_first_args(arg_count, arg_count_after, continue_block, iterable_type, iterator, temp_stack, visitor):
    builder = visitor.get_builder()
    # not_enough_values_error_block = builder.create_block("Not Enough Values Unpack Error")
    # too_many_values_error_block = builder.create_block("Too Many Values Unpack Error")
    test_next_block = builder.create_block("Test Next")
    for i in range(arg_count):
        builder.br(test_next_block)
        builder.set_insert_block(test_next_block)

        next_type, next_value = caller.call_obj(visitor, "__next__", iterator, iterable_type, [], [], {})
        temp_stack.append((next_type, next_value))

        # excp.py_runtime_clear_error(code_gen, builder)
        # test = builder.eq(next_value, null_ptr)
        # test_next_block = builder.create_block("Test Next")
        # builder.cond_br(test, not_enough_values_error_block, test_next_block)
        if i != arg_count - 1:
            test_next_block = builder.create_block("Test Next")
            builder.br(test_next_block)

        if i == arg_count - 1 and arg_count_after == -1:
            # builder.set_insert_block(test_next_block)
            # next_type, next_value = caller.call_obj(visitor, "__next__", iterator, iterable_type, [], [], {})
            # excp.py_runtime_clear_error(code_gen, builder)
            # test = builder.eq(next_value, null_ptr)
            # builder.cond_br(test, continue_block, too_many_values_error_block)
            builder.br(continue_block)  # to replace with a condbr when we will have a better support for exception

    # builder.set_insert_block(not_enough_values_error_block)
    # # "not enough values to unpack (expected " + arg_count + ", got " + i+1 + ")"
    # excp.raise_index_error(visitor) #TODO: give more info when raising the error

    # builder.set_insert_block(too_many_values_error_block)
    # # "too many values to unpack (expected " + arg_count + ")"
    # excp.raise_index_error(visitor) #TODO: give more info when raising the error


def unpack_rest_of_iterator_to_list(args_after, iterable_type, iterator, visitor):
    builder, code_gen = visitor.get_builder(), visitor.get_code_gen()
    unpack_rest_of_iterator = builder.create_block("Unpack rest of iterator")
    append_list = builder.create_block("Append List")
    array = gen_list.instanciate_python_list(code_gen, builder, builder.const_int64(0))
    array_type = get_list_of_python_obj_type()
    builder.br(unpack_rest_of_iterator)

    builder.set_insert_block(unpack_rest_of_iterator)
    next_type, next_value = caller.call_obj(visitor, "__next__", iterator, iterable_type, [], [], {})
    null_ptr = builder.const_null(code_type.get_py_obj_ptr(code_gen))
    test = builder.eq(next_value, null_ptr)
    builder.cond_br(test, args_after, append_list)

    builder.set_insert_block(append_list)
    py_obj_type, py_obj = runtime.value_to_pyobj(code_gen, builder, next_value, next_type)
    gen_list.python_list_append(visitor, array, py_obj_type, py_obj)
    builder.br(unpack_rest_of_iterator)

    return array_type, array


def get_sub_list(arg_count_after, array, array_type, array_length, visitor):
    builder, code_gen = visitor.get_builder(), visitor.get_code_gen()
    sub_list_length = builder.sub(array_length, builder.const_int64(arg_count_after))
    # If the list length is smaller than arg_count_after, then we should throw an error
    # "not enough values to unpack (expected at least 'arg_count_after', got 'list length')"
    lower_type, lower_value = runtime.value_to_pyobj(code_gen, builder, builder.const_int64(0), get_int_type())
    upper_type, upper_value = runtime.value_to_pyobj(code_gen, builder, sub_list_length, get_int_type())
    step_type, step_value = runtime.value_to_pyobj(code_gen, builder, builder.const_int64(1), get_int_type())
    slice_value = gen_slice.py_slice_new(visitor, lower_value, upper_value, step_value)
    sub_list_type, sub_list_value = caller.call_obj(visitor, "__getitem__", array, array_type, [slice_value],
                                                    [get_python_obj_type()], {})
    return sub_list_type, sub_list_value
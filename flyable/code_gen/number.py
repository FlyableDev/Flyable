from __future__ import annotations

from ast import NameConstant
from typing import TYPE_CHECKING

import flyable.code_gen.caller as caller
import flyable.code_gen.code_type as code_type
import flyable.code_gen.debug as debug
import flyable.code_gen.fly_obj as fly_obj
import flyable.code_gen.ref_counter as ref_counter
import flyable.code_gen.runtime as runtime
import flyable.code_gen.type as gen_type
import flyable.data.lang_type as lang_type
import flyable.data.type_hint as hint

if TYPE_CHECKING:
    from flyable.code_gen.code_gen import CodeGen
    from flyable.parse.parser_visitor import ParserVisitor

"""
Module related to the python number protocol
"""


def call_number_protocol(visitor: ParserVisitor, func_name: str, obj_type: lang_type.LangType, obj: int, instance_type: int, args_types: list[lang_type.LangType], args: list[int]):
    code_gen: CodeGen = visitor.get_code_gen()
    builder = visitor.get_builder()

    if not is_number_protocol_func(func_name):
        raise NameError("Unsupported protocol for function name " + func_name)

    nb_args = len(args)
    if is_number_inquiry_func_valid(func_name, nb_args):
        func_type = code_type.get_func(
            code_type.get_int32(), [code_type.get_py_obj_ptr(code_gen)]
        )
        protocol_result = visitor.generate_entry_block_var(code_type.get_int32())
    elif is_number_binary_func_valid(func_name, nb_args):
        func_type = code_type.get_func(
            code_type.get_py_obj_ptr(code_gen), [code_type.get_py_obj_ptr(code_gen)] * 2
        )
        protocol_result = visitor.generate_entry_block_var(
            code_type.get_py_obj_ptr(code_gen)
        )
    elif is_number_ternary_func_valid(func_name, nb_args):
        func_type = code_type.get_func(
            code_type.get_py_obj_ptr(code_gen), [code_type.get_py_obj_ptr(code_gen)] * 3
        )
        protocol_result = visitor.generate_entry_block_var(
            code_type.get_py_obj_ptr(code_gen)
        )
    else:
        raise TypeError(
            f"The given number of arguments ({args}) doesn't match the number of parameters required for {func_name}"
        )

    number_call_block = builder.create_block()
    number_call_2_block = builder.create_block()
    basic_call_block = builder.create_block()
    continue_block = builder.create_block()

    func_type = func_type.get_ptr_to()

    num_call_args = []
    num_call_args_types = []

    for i, (arg, arg_type) in enumerate(zip(args, args_types, strict=True)):
        new_type, new_value = runtime.value_to_pyobj(code_gen, builder, arg, arg_type)
        num_call_args.append(new_value)
        num_call_args_types.append(new_type)

    slot_id = get_number_slot_from_func_name(func_name)
    slot = builder.const_int64(slot_id)

    as_number = gen_type.py_object_type_get_tp_as_number_ptr(visitor, instance_type)
    as_number = builder.load(as_number)
    as_number = builder.ptr_cast(as_number, code_type.get_int8_ptr().get_ptr_to())
    is_number_null = builder.eq(
        as_number, builder.const_null(code_type.get_int8_ptr().get_ptr_to())
    )

    builder.cond_br(is_number_null, basic_call_block, number_call_block)
    builder.set_insert_block(number_call_block)
    func_to_call = builder.gep2(as_number, code_type.get_int8_ptr(), [slot])
    func_to_call = builder.load(func_to_call)
    func_to_call = builder.ptr_cast(func_to_call, func_type)

    # Check if the function that we got from the slot is not null

    is_func_null = builder.eq(func_to_call, builder.const_null(func_type))
    builder.cond_br(is_func_null, basic_call_block, number_call_2_block)

    builder.set_insert_block(number_call_2_block)
    builder.store(builder.call_ptr(func_to_call, [obj] + num_call_args), protocol_result)

    builder.br(continue_block)

    builder.set_insert_block(basic_call_block)

    # If the inquiry call isn't supported, then we fail the inquiry
    args_size = len(args)
    if is_number_inquiry_func_valid(func_name, args_size):
        builder.store(builder.const_int32(0), protocol_result)
    elif is_number_ternary_func_valid(func_name, args_size):
        basic_call_type, basic_call_value = caller.call_obj(visitor, func_name, obj, obj_type, num_call_args,
                                                            num_call_args_types, {}, False, False, False)
        if basic_call_value is None: 
            raise Exception("Could not call pow protocol")
        builder.store(basic_call_value, protocol_result)
    else:
        basic_call_type, basic_call_value = caller.call_obj(
            visitor,
            func_name,
            obj,
            obj_type,
            num_call_args,
            num_call_args_types,
            {},
            False,
            False,
        )

        if basic_call_value is None: 
            raise Exception("Could not call fallback protocol")

        builder.store(basic_call_value, protocol_result)
    builder.br(continue_block)

    builder.set_insert_block(continue_block)
    for num_call_arg, num_call_arg_type in zip(num_call_args, num_call_args_types):
        ref_counter.ref_decr_incr(visitor, num_call_arg_type, num_call_arg)

    if is_number_inquiry_func(func_name):
        return builder.int_cast(builder.load(protocol_result), code_type.get_int1())
    elif is_number_binary_func(func_name) or is_number_ternary_func_valid(func_name, args_size):
        return builder.load(protocol_result)
    elif is_number_ternary_func(func_name):
        return builder.load(protocol_result)
    else:
        raise NotImplementedError("Unsupported call protocol")


def is_py_obj_impl_number_protocol(visitor, obj_type, obj, instance_type=None):
    """
    Return the value if the number protocol is implemented. Also return the as_number value in case it could be
    re-used to avoid an extra load instruction.
    """
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    if instance_type is None:
        instance_type = fly_obj.get_py_obj_type(builder, obj)

    as_number = builder.load(
        gen_type.py_object_type_get_tp_as_number_ptr(visitor, instance_type)
    )
    impl_number_protocol = builder.eq(
        as_number, builder.const_null(code_type.get_py_obj_ptr(code_gen))
    )
    return impl_number_protocol, as_number


def is_call_valid_for_number_protocol(func_name: str, args_count: int) -> bool:
    return (
            (is_number_ternary_func(func_name) and args_count == 2)
            or (is_number_inquiry_func(func_name) and args_count == 0)
            or (is_number_unary_func(func_name) and args_count == 0)
            or (is_number_binary_func(func_name) and args_count == 1)
    )


def is_number_protocol_func(func_name: str) -> bool:
    return (
            is_number_binary_func(func_name)
            or is_number_inquiry_func(func_name)
            or is_number_ternary_func(func_name)
    )


def is_number_binary_func(func_name: str) -> bool:
    """
    returns if the function name is a binary function from the number protocol
    """
    # TODO: Put all binary cases
    binary_numb_funcs = {
        "__add__",
        "__sub__",
        "__mul__",
        "__div__",
        "__mod__",
        "__bool__",
        "__inv__",
        "__lshift__",
        "__rshift__",
        "__and__",
        "__xor__",
        "__or__",
    }
    return func_name in binary_numb_funcs


def is_number_inquiry_func(func_name: str) -> bool:
    return func_name == "__bool__"


def is_number_ternary_func(func_name: str) -> bool:
    names = {"__pow__", "__in_pow__"}
    return func_name in names


def is_number_unary_func(func_name: str) -> bool:
    names = {"__neg__", "__pos__", "__abs__", "__int__", "__float__"}
    return func_name in names


def is_number_binary_func_valid(func_name: str, len_args: int) -> bool:
    """
    returns if the function name is a valid binary function from the number protocol
    """
    return is_number_binary_func(func_name) and len_args == 1


def is_number_ternary_func_valid(func_name: str, len_args: int) -> bool:
    """
    returns if the function name is a valid ternary function from the number protocol
    """
    return is_number_ternary_func(func_name) and len_args == 2


def is_number_inquiry_func_valid(func_name: str, len_args: int) -> bool:
    """
    returns if the function name is a valid inquiry function from the number protocol
    """
    return is_number_unary_func(func_name) and len_args == 0


def handle_pow_func_special_case(func_name: str, args: list, args_type: list, visitor: ParserVisitor) -> bool:
    """
    utility function to ensure the rigth number of args are passed to the pow function and adds None if there was one missing\n
    This function makes sure that the function name is indeed __pow__ before doing the operation\n
    Returns: True if the name is __pow__ and the args, after formatting, are valid
    False if the name isn't __pow__ or the args cannot be formatted to match the valid format
    """
    if func_name != "__pow__":
        return False

    if len(args) == 1:
        none = visitor.get_code_gen().get_none()
        none_var = visitor.get_builder().global_var(none)
        args.append(visitor.get_builder().load(none_var))
        args_type.append(lang_type.get_none_type())

    return len(args) == 2


def get_number_slot_from_func_name(func_name: str) -> int:
    slots = {
        "__add__": 0,
        "__sub__": 1,
        "__mul__": 2,
        "__mod__": 3,
        "__divmod__": 4,
        "__pow__": 5,
        "__div__": 6,
        "__pos__": 7,
        "__abs__": 8,
        "__bool__": 9,
        "__lshift__": 11,
        "__rshift__": 12,
        "__and__": 13,
        "__xor__": 14,
        "__or__": 15,
    }

    return slots[func_name]

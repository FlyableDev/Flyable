from __future__ import annotations
from typing import TYPE_CHECKING
import flyable.code_gen.caller as caller
import flyable.code_gen.code_type as code_type
import flyable.code_gen.runtime as runtime
import flyable.code_gen.type as gen_type
import flyable.code_gen.ref_counter as ref_counter
from flyable.data.lang_type import LangType

if TYPE_CHECKING:
    from flyable.parse.parser import ParserVisitor

"""
Module to handle the Python rich compare protocol
"""


def is_func_name_rich_compare(func_name: str):
    return get_rich_compare_slots_from_func_name(func_name) is not None


def get_rich_compare_slots_from_func_name(func_name: str):
    slots = {"__gt__": 4,
             "__lt__": 0,
             "__eq__": 2,
             "__ne__": 3,
             "__le__": 1,
             "__ge__": 5}
    if func_name in slots:
        return slots[func_name]
    return None


def call_rich_compare_protocol(visitor: ParserVisitor, func_name: str, obj_type: LangType, obj: int, instance_type: int, args_types: list[LangType], args: list[int]):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    protocol_result = visitor.generate_entry_block_var(code_type.get_py_obj_ptr(code_gen))

    num_call_args = []
    num_call_args_types = []

    for i, e in enumerate(args):
        new_type, new_value = runtime.value_to_pyobj(visitor, args[i], args_types[i])
        num_call_args.append(new_value)
        num_call_args_types.append(new_type)

    rich_compare_slots = get_rich_compare_slots_from_func_name(func_name)
    if rich_compare_slots is None:
        raise Exception("Rich compare slot is None")
        
    slot = builder.const_int32(rich_compare_slots)

    rich_compare_func = gen_type.py_object_type_get_tp_richcompare_ptr(visitor, instance_type)
    rich_compare_func = builder.load(rich_compare_func)
    is_compare_null = builder.eq(rich_compare_func, builder.const_null(code_type.get_int8_ptr()))

    basic_call_block = builder.create_block()
    compare_call_block = builder.create_block()

    builder.cond_br(is_compare_null, basic_call_block, compare_call_block)

    builder.set_insert_block(compare_call_block)
    func_type = code_type.get_func(code_type.get_py_obj_ptr(code_gen),
                                   [code_type.get_py_obj_ptr(code_gen), code_type.get_py_obj_ptr(code_gen),
                                    code_type.get_int32()])
    func_type = func_type.get_ptr_to()
    func_to_call = builder.ptr_cast(rich_compare_func, func_type)

    continue_block = builder.create_block()
    builder.store(builder.call_ptr(func_to_call, [obj] + num_call_args + [slot]), protocol_result)
    builder.br(continue_block)

    builder.set_insert_block(basic_call_block)
    basic_call_type, basic_call_value = caller.call_obj(visitor, func_name, obj, obj_type, num_call_args,
                                                        num_call_args_types, {}, False, False)
    builder.store(basic_call_value, protocol_result)
    builder.br(continue_block)

    builder.set_insert_block(continue_block)
    for i in range(len(num_call_args)):
        ref_counter.ref_decr_incr(visitor, num_call_args_types[i], num_call_args[i])
    return builder.load(protocol_result)

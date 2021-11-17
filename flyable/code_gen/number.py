import flyable.code_gen.type as gen_type
import flyable.data.type_hint as hint
import flyable.code_gen.runtime as runtime
import flyable.code_gen.debug as debug
import flyable.code_gen.fly_obj as fly_obj
import flyable.code_gen.code_type as code_type
import flyable.code_gen.type as gen_type
import flyable.code_gen.ref_counter as ref_counter
import flyable.code_gen.caller as caller
import flyable.data.lang_type as lang_type

"""
Module related to the python number protocol
"""


def call_number_protocol(visitor, func_name, obj_type, obj, instance_type, args_types, args):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    protocol_result = visitor.generate_entry_block_var(code_type.get_py_obj_ptr(code_gen))

    num_call_args = []
    num_call_args_types = []

    for i, e in enumerate(args):
        new_type, new_value = runtime.value_to_pyobj(
            code_gen, builder, args[i], args_types[i])
        num_call_args.append(new_value)
        num_call_args_types.append(new_type)

    slot_id = get_number_slot_from_func_name(func_name)
    slot = builder.const_int64(slot_id)

    as_number = gen_type.py_object_type_get_tp_as_number_ptr(
        visitor, instance_type)
    as_number = builder.load(as_number)
    as_number = builder.ptr_cast(
        as_number, code_type.get_int8_ptr().get_ptr_to())

    is_number_null = builder.eq(as_number, builder.const_null(
        code_type.get_int8_ptr().get_ptr_to()))

    basic_call_block = builder.create_block()
    number_call_block = builder.create_block()

    builder.cond_br(is_number_null, basic_call_block, number_call_block)
    builder.set_insert_block(number_call_block)
    func_to_call = builder.gep2(as_number, code_type.get_int8_ptr(), [slot])
    func_to_call = builder.load(func_to_call)
    func_type = code_type.get_func(code_type.get_py_obj_ptr(code_gen), [code_type.get_py_obj_ptr(code_gen)] * 2)
    func_type = func_type.get_ptr_to()
    func_to_call = builder.ptr_cast(func_to_call, func_type)

    # Check if the function that we got from the slot is not null
    number_call_2_block = builder.create_block()
    is_func_null = builder.eq(func_to_call, builder.const_null(func_type))
    builder.cond_br(is_func_null, basic_call_block, number_call_2_block)

    continue_block = builder.create_block()
    builder.set_insert_block(number_call_2_block)
    builder.store(builder.call_ptr(func_to_call, [obj] + num_call_args), protocol_result)
    builder.br(continue_block)

    builder.set_insert_block(basic_call_block)
    basic_call_type, basic_call_value = caller.call_obj(visitor, func_name, obj, obj_type, num_call_args,
                                                        num_call_args_types, False, False)
    builder.store(basic_call_value, protocol_result)
    builder.br(continue_block)

    builder.set_insert_block(continue_block)
    for i in range(len(num_call_args)):
        ref_counter.ref_decr_incr(
            visitor, num_call_args_types[i], num_call_args[i])
    return builder.load(protocol_result)


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
        gen_type.py_object_type_get_tp_as_number_ptr(visitor, instance_type))
    impl_number_protocol = builder.eq(
        as_number, builder.const_null(code_type.get_py_obj_ptr(code_gen)))
    return impl_number_protocol, as_number


def is_call_valid_for_number_protocol(func_name, args_count):
    if is_number_func_ternary(func_name) and args_count == 2:
        return True
    elif is_number_func_inquiry(func_name) and args_count == 0:
        return True
    elif is_number_func_unary(func_name) and args_count == 0:
        return True
    elif is_number_binary_func(func_name) and args_count == 1:
        return True
    return False


def is_number_protocol_func(func_name):
    return is_number_binary_func(func_name) or is_number_func_inquiry(func_name) or is_number_func_ternary(func_name)


def is_number_binary_func(func_name):
    """
    returns if the function name is a binary function from the number protocol
    """
    # TODO: Put all binary cases
    binary_numb_funcs = {"__add__", "__sub__", "__mul__", "__div__", "__mod__", "__bool__", "__inv__", "__lshift__",
                         "__rshift__", "_and", "__xor__", "__or__", }
    return func_name in binary_numb_funcs


def is_number_func_inquiry(func_name):
    return func_name == "__bool__"


def is_number_func_ternary(func_name):
    names = {"__pow__", "__in_pow__"}
    return func_name in names


def is_number_func_unary(func_name):
    names = {"__neg__", "__pos__", "__abs__", "__int__", "__float__"}
    return func_name in names


def get_number_slot_from_func_name(func_name):
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
        "__rshitf__": 12,
        "_and": 13,
        "__xor__": 14,
        "__or__": 15,
    }

    return slots[func_name]

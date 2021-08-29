import flyable.code_gen.type as gen_type
import flyable.data.type_hint as hint
import flyable.code_gen.runtime as runtime
import flyable.code_gen.debug as debug
import flyable.code_gen.fly_obj as fly_obj
import flyable.code_gen.code_type as code_type
import flyable.code_gen.type as gen_type
import flyable.code_gen.ref_counter as ref_counter
import flyable.data.lang_type as lang_type

"""
Module related to the python number protocol
"""


def call_number_protocol(visitor, func_name, obj_type, obj, instance_type, args_types, args):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    num_call_args = []
    num_call_args_types = []

    for i, e in enumerate(args):
        new_type, new_value = runtime.value_to_pyobj(code_gen, builder, args[i], args_types[i])
        num_call_args.append(new_value)
        num_call_args_types.append(new_type)

    slot = builder.const_int64(get_number_slot_from_func_name(func_name))

    as_number = gen_type.py_object_type_get_tp_as_number_ptr(visitor, instance_type)
    as_number = builder.load(as_number)
    as_number = builder.ptr_cast(as_number, code_type.get_int8_ptr().get_ptr_to())

    if is_number_binary_func(func_name) and len(args) == 1:  # Binary func only take on arg
        func_to_call = builder.gep2(as_number, code_type.get_int8_ptr(), [slot])
        func_to_call = builder.load(func_to_call)
        func_type = code_type.get_func(code_type.get_py_obj_ptr(code_gen), [code_type.get_py_obj_ptr(code_gen)] * 2)
        func_type = func_type.get_ptr_to()
        func_to_call = builder.ptr_cast(func_to_call, func_type)

        for i in range(len(num_call_args)):
            ref_counter.ref_decr_incr(visitor, num_call_args_types[i], num_call_args[i])

        return builder.call_ptr(func_to_call, [obj] + num_call_args)


def is_py_obj_impl_number_protocol(visitor, obj_type, obj, instance_type=None):
    """
    Return the value if the number protocol is implemented. Also return the as_number value in case it could be
    re-used to avoid an extra load instruction.
    """
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    if instance_type is None:
        instance_type = fly_obj.get_py_obj_type(builder, obj)

    as_number = builder.load(gen_type.py_object_type_get_tp_as_number_ptr(visitor, instance_type))
    impl_number_protocol = builder.eq(as_number, builder.const_null(code_type.get_py_obj_ptr(code_gen)))
    return impl_number_protocol, as_number


def is_type_impl_number_protocol(visitor, lang_type):
    if hint.is_python_type(lang_type, "builtins.int") or hint.is_python_type(lang_type, "builtins.float"):
        return True
    return False


def is_number_protocol_func(func_name):
    return is_number_binary_func(func_name)


def is_number_binary_func(func_name):
    """
    returns if the function name is a binary function from the number protocol
    """
    # TODO: Put all binary cases
    binary_numb_funcs = ["__add__", "__sub__", "__mul__", "__div__", "__mod__"]
    return func_name in binary_numb_funcs


def get_number_slot_from_func_name(func_name):
    slots = {
        "__add__": 0,
        "__sub__": 1
    }
    return slots[func_name]

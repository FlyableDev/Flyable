"""
Module that handles function calls.
Specifically Python ones
"""
import flyable.code_gen.code_type as code_type
import flyable.code_gen.tuple as tuple_call
import flyable.code_gen.code_type as code_type
from flyable.code_gen.code_type import CodeType
import flyable.code_gen.code_gen as gen
import flyable.code_gen.exception as excp


def call_obj(code_gen, builder, func_name, obj, obj_type, args, args_type):
    """
    Call a method independent from the called type.
    There is 3 calls scenario:
    - Direct flyable method call
    - Virtual flyable method call
    - Python runtime method call
    """
    if obj_type.is_obj():
        # Traditional call
        called_class = code_gen.get_data().get_class(obj_type.get_id())
        called_func = called_class.get_func(func_name)
        called_impl = None
        if called_func is not None:
            found_impl = None
            for impl in called_func.impls_iter():
                if called_func.get_args_count() == len(args):
                    match_arg = True
                    for i, arg in enumerate(impl.args_iter()):
                        if arg != args_type[i]:
                            match_arg = False
                    if match_arg:
                        called_impl = impl
            if called_impl is not None:
                builder.call(called_impl.get_code_func(), args)
    elif obj_type.is_python_obj():
        # Python call
        return generate_python_method_call(code_gen, builder, func_name, obj, args)
    else:
        raise ValueError("Type un-callable: " + obj_type.to_str(code_gen.get_data()))


def generate_python_method_call(code_gen, builder, name, obj, args):
    # Get the function first
    # TODO : Rely on GetAttr with pre-initialized Python string is certainly faster
    get_attr_args = [code_type.get_int8_ptr(), code_type.get_int8_ptr()]
    get_attr_func = code_gen.get_or_create_func("PyObject_GetAttrString", code_type.get_int8_ptr(), get_attr_args,
                                                gen.Linkage.EXTERNAL)

    attr_str = builder.ptr_cast(builder.global_str(name + "\0"), code_type.get_int8_ptr())
    attr_obj = builder.call(get_attr_func, [obj, attr_str])

    return generate_python_call(code_gen, builder, attr_obj, args)


def generate_python_call(code_gen, builder, callable, args):
    # TODO : Relying on vectorcall is probably faster than calling PyObject_Call
    call_funcs_args = [code_type.get_int8_ptr()] * 3
    call_func = code_gen.get_or_create_func("PyObject_Call", code_type.get_int8_ptr(), call_funcs_args,
                                            gen.Linkage.EXTERNAL)

    arg_list = tuple_call.python_tuple_new(code_gen, builder, builder.const_int64(len(args)))
    for i, e in enumerate(args):
        tuple_call.python_tuple_set_unsafe(code_gen, builder, arg_list, builder.const_int64(i), e)
    result = builder.call(call_func, [callable, arg_list, builder.const_null(code_type.get_int8_ptr())])
    # excp.py_runtime_print_error(code_gen, builder)
    return result

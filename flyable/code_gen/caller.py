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
import flyable.parse.adapter as adapter
import flyable.data.lang_type as lang_type
import flyable.code_gen.runtime as runtime
import copy


def call_obj(code_gen, builder, parser, func_name, obj, obj_type, args, args_type, optional=False):
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
        if called_func is None and optional:
            return None, None
        called_impl = adapter.adapt_func(called_func, args_type, code_gen.get_data(), parser)
        return called_impl.get_return_type(), builder.call(called_impl.get_code_func(), args)
    elif obj_type.is_python_obj() or obj_type.is_collection():
        # Python call
        py_args = copy.copy(args)
        py_args_type = copy.copy(args_type)
        # For python objects we need to remove the first args
        py_args.pop(0)
        py_args_type.pop(0)

        for i, arg in enumerate(py_args):
            py_args[i] = runtime.value_to_pyobj(code_gen, builder, arg, py_args_type[i])

        return lang_type.get_python_obj_type(), generate_python_method_call(code_gen, builder, func_name, obj, py_args)
    else:
        raise ValueError("Type un-callable: " + obj_type.to_str(code_gen.get_data()))


def generate_python_method_call(code_gen, builder, name, obj, args):
    # Get the function first

    get_attr_args = [code_type.get_py_obj_ptr(code_gen), code_type.get_py_obj_ptr(code_gen)]
    get_attr_func = code_gen.get_or_create_func("PyObject_GetAttr", code_type.get_py_obj_ptr(code_gen), get_attr_args,
                                                gen.Linkage.EXTERNAL)

    attr_str = builder.global_var(code_gen.get_or_insert_str(name))
    attr_str = builder.load(attr_str)
    attr_obj = builder.call(get_attr_func, [obj, attr_str])
    #excp.py_runtime_print_error(code_gen, builder)
    return generate_python_call(code_gen, builder, attr_obj, args)


def generate_python_call(code_gen, builder, callable, args):
    # TODO : Relying on vectorcall is probably faster than calling PyObject_Call
    call_funcs_args = [code_type.get_py_obj_ptr(code_gen)] * 3
    call_func = code_gen.get_or_create_func("PyObject_Call", code_type.get_py_obj_ptr(code_gen), call_funcs_args,
                                            gen.Linkage.EXTERNAL)
    arg_list = tuple_call.python_tuple_new(code_gen, builder, builder.const_int64(len(args)))
    for i, e in enumerate(args):
        tuple_call.python_tuple_set_unsafe(code_gen, builder, arg_list, builder.const_int64(i), e)
    result = builder.call(call_func, [callable, arg_list, builder.const_null(code_type.get_py_obj_ptr(code_gen))])
    return result

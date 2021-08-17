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
import flyable.code_gen.debug as debug
import flyable.parse.adapter as adapter
import flyable.data.lang_type as lang_type
import flyable.code_gen.runtime as runtime
import flyable.parse.shortcut as shortcut
import copy
import flyable.code_gen.function as function
import flyable.code_gen.fly_obj as fly_obj
import flyable.data.type_hint as hint
import flyable.code_gen.number as num


def call_obj(visitor, func_name, obj, obj_type, args, args_type, optional=False):
    """
    Call a method independent from the called type.
    There is 3 calls scenario:
    - Direct flyable method call
    - Virtual flyable method call
    - Python runtime method call
    """
    if obj_type.is_obj():
        # Traditional and direct obj call
        called_class = visitor.get_data().get_class(obj_type.get_id())
        called_func = called_class.get_func(func_name)
        if called_func is None and optional:
            return None, None
        called_impl = adapter.adapt_func(called_func, [obj_type] + args_type, visitor.get_data(), visitor.get_parser())
        return_type = called_impl.get_return_type()
        return_type.add_hint(hint.TypeHintRefIncr())
        return return_type, visitor.get_builder().call(called_impl.get_code_func(), [obj] + args)
    elif obj_type.is_python_obj() or obj_type.is_collection():
        # Maybe there is a shortcut available to skip the python call

        found_shortcut = shortcut.get_obj_call_shortcuts(obj_type, args_type, func_name)
        if found_shortcut is not None:
            return found_shortcut.parse(visitor, obj_type, obj, copy.copy(args_type), copy.copy(args))

        # Special case where the call is a binary number protocol
        if num.is_number_protocol_func(func_name) and num.is_type_impl_number_protocol(visitor, obj_type):
            instance_type = fly_obj.get_py_obj_type(visitor.get_builder(), obj)
            return lang_type.get_python_obj_type(), num.call_number_protocol(visitor, func_name, obj_type, obj,
                                                                             instance_type, args_type,args)

        # Python call
        py_args = copy.copy(args)

        for i, arg in enumerate(py_args):
            py_args[i] = runtime.value_to_pyobj(visitor.get_code_gen(), visitor.get_builder(), arg, args_type[i])
        return_type = lang_type.get_python_obj_type()
        return_type.add_hint(hint.TypeHintRefIncr())
        return return_type, generate_python_call(visitor, obj, func_name, py_args)
    else:
        raise ValueError("Type un-callable: " + obj_type.to_str(visitor.get_data()) + " for method " + func_name)


# https://docs.python.org/3/c-api/method.html
def generate_python_call(visitor, obj, func_name, args):
    code_gen, builder = visitor.get_code_gen(), visitor.get_builder()

    # the found attribute is the callable function
    func_to_call = fly_obj.py_obj_get_attr(visitor, obj, func_name)

    call_result_var = visitor.generate_entry_block_var(code_type.get_py_obj_ptr(code_gen))

    vector_call_block = builder.create_block()
    tp_call_block = builder.create_block()
    continue_block = builder.create_block()

    callable_type = fly_obj.get_py_obj_type(visitor.get_builder(), func_to_call)

    tp_flag = function.py_obj_type_get_tp_flag_ptr(visitor, callable_type)
    tp_flag = builder.load(tp_flag)

    can_vec = builder._and(tp_flag, builder.const_int32(2048))  # Does the type flags contain Py_TPFLAGS_HAVE_VECTORCALL
    can_vec = builder.eq(can_vec, builder.const_int32(0))

    # If it's non-zero then it has the feature
    builder.cond_br(can_vec, tp_call_block, vector_call_block)

    builder.set_insert_block(vector_call_block)
    vec_result = function.call_py_func_vec_call(visitor, func_to_call, args, callable_type)
    builder.store(vec_result, call_result_var)
    builder.br(continue_block)

    builder.set_insert_block(tp_call_block)
    tp_result = function.call_py_func_tp_call(visitor, func_to_call, args)
    builder.store(tp_result, call_result_var)
    builder.br(continue_block)

    builder.set_insert_block(continue_block)

    result = builder.load(call_result_var)
    # excp.py_runtime_print_error(code_gen, builder)
    # excp.check_excp(visitor, result)
    return result

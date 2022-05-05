import copy

import flyable.code_gen.fly_obj as fly_obj
import flyable.code_gen.exception as excp
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen
import flyable.code_gen.tuple as tuple_call
import flyable.code_gen.dict as dict_call
import flyable.code_gen.type as gen_type
import flyable.code_gen.debug as debug
import flyable.code_gen.ref_counter as ref_counter
import flyable.code_gen.runtime as runtime
import flyable.data.lang_type as lang_type


def check_py_obj_is_func_type(visitor, func_to_call: int):
    obj_type = fly_obj.get_py_obj_type(visitor.get_builder(), func_to_call)
    func_type = visitor.get_builder().global_var(visitor.get_code_gen().get_py_func_type())
    return visitor.get_builder().eq(obj_type, func_type)


def get_vector_call_ptr(visitor, python_callable: int):
    """
    Retrieves vector call pointer from Python callable.
    :param visitor: Parser visitor
    :param python_callable: Python callable
    :return: Loaded vector call pointer
    """
    builder = visitor.get_builder()

    func_py_obj_type = fly_obj.get_py_obj_type(builder, python_callable)

    vector_call_offset = builder.load(gen_type.py_object_type_get_vectorcall_offset_ptr(visitor, func_py_obj_type))

    callable_ptr = builder.ptr_cast(python_callable, code_type.get_int8_ptr())
    vector_call = builder.gep2(callable_ptr, code_type.get_int8(), [vector_call_offset])
    vector_call_ptr = builder.ptr_cast(vector_call,
                                       code_type.get_vector_call_func(visitor.get_code_gen()).get_ptr_to().get_ptr_to())
    return builder.load(vector_call_ptr)


def call_py_func_vec_call(visitor, obj: int, func_to_call: int, args: list[int], kwargs: dict[int, int],
                          vector_call_ptr: int):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    # Allocate memory for the args on the stack so it's much faster
    args_stack_memory = visitor.generate_entry_block_var(
        code_type.get_array_of(code_type.get_py_obj_ptr(code_gen), len(args) + len(kwargs) + 1))
    builder.store(obj, builder.gep(args_stack_memory, builder.const_int32(0), builder.const_int32(0)))
    # Python docs recommend the use of the offset for more efficient call
    args_stack_memory = builder.gep(args_stack_memory, builder.const_int32(0), builder.const_int32(1))

    # Set the args into the stack memory
    for i, arg in enumerate(args):
        arg_gep = builder.gep2(args_stack_memory, code_type.get_py_obj_ptr(code_gen), [builder.const_int32(i)])
        builder.store(arg, arg_gep)

    for i, kwarg in enumerate(kwargs.values()):
        kwarg_gep = builder.gep2(args_stack_memory, code_type.get_py_obj_ptr(code_gen),
                                 [builder.const_int32(i + len(args))])
        builder.store(kwarg, kwarg_gep)

    # Cast the stack memory to simplify the type
    args_stack_memory = builder.ptr_cast(args_stack_memory, code_type.get_py_obj_ptr(code_gen).get_ptr_to())

    # nargs is the size of the arguments with the PY_VECTORCALL_ARGUMENTS_OFFSET
    arguments_offset = builder.const_int64(-9223372036854775808)
    nargs = builder._or(builder.const_int64(len(args)), arguments_offset)

    if kwargs:
        kw_names = tuple_call.python_tuple_new_alloca(visitor, len(kwargs))
        for i, key in enumerate(kwargs.keys()):
            tuple_call.python_tuple_set_unsafe(visitor, kw_names, builder.const_int64(i), key)
    else:
        kw_names = builder.const_null(code_type.get_py_obj_ptr(code_gen))

    vec_args = [func_to_call, args_stack_memory, nargs, kw_names]

    result = builder.call_ptr(vector_call_ptr, vec_args)

    return result


def call_py_func_tp_call(visitor, obj: int, func_to_call: int, args: list[int], kwargs: dict[int, int]):
    """
    Call a python function using the tp_call convention
    """
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()
    arg_list = tuple_call.python_tuple_new_alloca(visitor, len(args))
    kwargs_list = builder.const_null(code_type.get_py_obj_ptr(code_gen))

    for i, e in enumerate(args):
        tuple_call.python_tuple_set_unsafe(visitor, arg_list, builder.const_int64(i), e)

    if kwargs:
        kwargs_list = dict_call.python_dict_new(visitor)
        for k, v in kwargs.items():
            dict_call.python_dict_set_item(visitor, kwargs_list, k, v)

    func_to_call_type = fly_obj.get_py_obj_type(visitor.get_builder(), func_to_call)

    tp_call_ptr = visitor.get_builder().load(py_obj_type_get_tp_call(visitor, func_to_call_type))

    args_types = [code_type.get_py_obj_ptr(code_gen)] * 3
    ty_call_ptr = builder.ptr_cast(tp_call_ptr,
                                   code_type.get_func(code_type.get_py_obj_ptr(code_gen), args_types).get_ptr_to())

    tp_args = [func_to_call, arg_list, kwargs_list]

    result = builder.call_ptr(ty_call_ptr, tp_args)

    return result


def py_obj_func_get_vectorcall_ptr(visitor, func: int):
    func = visitor.get_builder().ptr_cast(func, visitor.get_code_gen().get_py_func_struct().to_code_type().get_ptr_to())
    gep_indices = [visitor.get_builder().const_int32(0), visitor.get_builder().const_int32(14)]
    return visitor.get_builder().gep2(func, visitor.get_code_gen().get_py_func_struct().to_code_type(), gep_indices)


def py_obj_type_get_tp_call(visitor, func_type: int):
    func_type = visitor.get_builder().ptr_cast(func_type,
                                               visitor.get_code_gen().get_python_type().to_code_type().get_ptr_to())
    gep_indices = [visitor.get_builder().const_int32(0), visitor.get_builder().const_int32(16)]
    return visitor.get_builder().gep2(func_type, visitor.get_code_gen().get_python_type().to_code_type(), gep_indices)


def py_obj_type_get_tp_flag_ptr(visitor, func_type: int):
    func_type = visitor.get_builder().ptr_cast(func_type,
                                               visitor.get_code_gen().get_python_type().to_code_type().get_ptr_to())
    gep_indices = [visitor.get_builder().const_int32(0), visitor.get_builder().const_int32(21)]
    return visitor.get_builder().gep2(func_type, visitor.get_code_gen().get_python_type().to_code_type(), gep_indices)


def is_py_obj_method(visit, obj: int):
    """
    Return a value containing if obj is a python method
    """
    code_gen = visit.get_code_gen()
    builder = visit.get_builder()
    obj_type = fly_obj.get_py_obj_type(builder, obj)
    return builder.eq(obj_type, builder.global_var(code_gen.get_method_type()))


def py_function_get_globals(visitor, func_obj: int):
    """Return the globals dictionary associated with the function object func_obj."""
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    func = builder.ptr_cast(func_obj, code_gen.get_python_function_object_struct().to_code_type().get_ptr_to())
    gep_indices = [builder.const_int32(0), builder.const_int32(2)]

    result = builder.gep2(func, code_gen.get_python_function_object_struct().to_code_type(), gep_indices)
    return builder.load(result)


def py_function_get_builtins(visitor, func_obj):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()
    func = builder.ptr_cast(func_obj, code_gen.get_python_function_object_struct().to_code_type().get_ptr_to())
    gep_indices = [builder.const_int32(0), builder.const_int32(3)]
    result = builder.gep2(func, code_gen.get_python_function_object_struct().to_code_type(), gep_indices)
    return builder.load(result)


def py_dict_get_item(visitor, d: int, k: int):
    """Gets the value associated with key from the dictionary.

    Args:
        visitor (ParserVisitor): Parser visitor
        d (int): Dictionary
        k (int): Key
    """
    return runtime.pydict_getitem(visitor.get_code_gen(), visitor.get_builder(), d, k)

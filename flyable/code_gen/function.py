import copy

import flyable.code_gen.fly_obj as fly_obj
import flyable.code_gen.exception as excp
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen
import flyable.code_gen.tuple as tuple_call
import flyable.code_gen.type as gen_type
import flyable.code_gen.debug as debug
import flyable.code_gen.ref_counter as ref_counter
import flyable.data.lang_type as lang_type


def check_py_obj_is_func_type(visitor, func_to_call):
    obj_type = fly_obj.get_py_obj_type(visitor.get_builder(), func_to_call)
    func_type = visitor.get_builder().global_var(visitor.get_code_gen().get_py_func_type())
    return visitor.get_builder().eq(obj_type, func_type)


def call_py_func_vec_call(visitor, obj, func_to_call, args, func_to_call_type=None):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    if func_to_call_type is None:
        func_to_call_type = fly_obj.get_py_obj_type(builder, func_to_call)

    offset = builder.load(gen_type.py_object_type_get_vectorcall_offset_ptr(visitor, func_to_call_type))

    func_to_call_i8_ptr = builder.ptr_cast(func_to_call, code_type.get_int8_ptr())
    offset_result = builder.gep2(func_to_call_i8_ptr, code_type.get_int8(), [offset])
    vec_call = builder.ptr_cast(offset_result,
                                code_type.get_vector_call_func(visitor.get_code_gen()).get_ptr_to().get_ptr_to())
    vec_call = builder.load(vec_call)

    # Allocate memory for the args on the stack so it's much faster
    args_stack_memory = visitor.generate_entry_block_var(
        code_type.get_array_of(code_type.get_py_obj_ptr(code_gen), len(args) + 1))
    builder.store(obj, builder.gep(args_stack_memory, builder.const_int32(0), builder.const_int32(0)))
    # Python docs recommend the use of the offset for more efficient call
    args_stack_memory = builder.gep(args_stack_memory, builder.const_int32(0), builder.const_int32(1))

    # Set the args into the stack memory
    for i, e in enumerate(args):
        arg_gep = builder.gep2(args_stack_memory, code_type.get_py_obj_ptr(code_gen), [builder.const_int32(i)])
        builder.store(e, arg_gep)

    # Cast the stack memory to simplify the type
    args_stack_memory = builder.ptr_cast(args_stack_memory, code_type.get_py_obj_ptr(code_gen).get_ptr_to())

    # nargs is the size of the arguments with the PY_VECTORCALL_ARGUMENTS_OFFSET
    arguments_offset = builder.const_int64(-9223372036854775808)
    nargs = builder._or(builder.const_int64(len(args)), arguments_offset)
    vec_args = [func_to_call, args_stack_memory, nargs, builder.const_null(code_type.get_py_obj_ptr(code_gen))]

    result = builder.call_ptr(vec_call, vec_args)
    return result


def call_py_func_tp_call(visitor, obj, func_to_call, args):
    """
    Call a python function using the tp_call convention
    """
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()
    arg_list = tuple_call.python_tuple_new_alloca(visitor, len(args))
    for i, e in enumerate(args):
        tuple_call.python_tuple_set_unsafe(visitor, arg_list, i, e)

    kwargs = builder.const_null(code_type.get_py_obj_ptr(code_gen))  # Null kwargs

    func_to_call_type = fly_obj.get_py_obj_type(visitor.get_builder(), func_to_call)

    tp_call_ptr = visitor.get_builder().load(py_obj_type_get_tp_call(visitor, func_to_call_type))

    args_types = [code_type.get_py_obj_ptr(code_gen)] * 3
    ty_call_ptr = builder.ptr_cast(tp_call_ptr,
                                   code_type.get_func(code_type.get_py_obj_ptr(code_gen), args_types).get_ptr_to())

    tp_args = [func_to_call, arg_list, kwargs]

    result = builder.call_ptr(ty_call_ptr, tp_args)

    return result


def py_obj_func_get_vectorcall_ptr(visitor, func):
    func = visitor.get_builder().ptr_cast(func, visitor.get_code_gen().get_py_func_struct().to_code_type().get_ptr_to())
    gep_indices = [visitor.get_builder().const_int32(0), visitor.get_builder().const_int32(14)]
    return visitor.get_builder().gep2(func, visitor.get_code_gen().get_py_func_struct().to_code_type(), gep_indices)


def py_obj_type_get_tp_call(visitor, func_type):
    func_type = visitor.get_builder().ptr_cast(func_type,
                                               visitor.get_code_gen().get_python_type().to_code_type().get_ptr_to())
    gep_indices = [visitor.get_builder().const_int32(0), visitor.get_builder().const_int32(16)]
    return visitor.get_builder().gep2(func_type, visitor.get_code_gen().get_python_type().to_code_type(),
                                      gep_indices)


def py_obj_type_get_tp_flag_ptr(visitor, func_type):
    func_type = visitor.get_builder().ptr_cast(func_type,
                                               visitor.get_code_gen().get_python_type().to_code_type().get_ptr_to())
    gep_indices = [visitor.get_builder().const_int32(0), visitor.get_builder().const_int32(21)]
    return visitor.get_builder().gep2(func_type, visitor.get_code_gen().get_python_type().to_code_type(),
                                      gep_indices)


def is_py_obj_method(visit, obj):
    """
    Return a value containing if obj is a python method
    """
    code_gen = visit.get_code_gen()
    builder = visit.get_builder()
    obj_type = fly_obj.get_py_obj_type(visit, obj)
    return builder.eq(obj_type, builder.global_var(code_gen.get_method_type()))

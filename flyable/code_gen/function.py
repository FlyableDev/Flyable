import flyable.code_gen.fly_obj as fly_obj
import flyable.code_gen.exception as excp
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen
import flyable.code_gen.tuple as tuple_call


def check_py_obj_is_func_type(visitor, func_to_call):
    obj_type = fly_obj.get_py_obj_type(visitor.get_builder(), func_to_call)
    func_type = visitor.get_builder().global_var(visitor.get_code_gen().get_py_func_type())
    return visitor.get_builder().eq(obj_type, func_type)


def call_py_func_vec_call(visitor, func_to_call, args):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    vec_call = py_obj_func_get_vectorcall_ptr(visitor, func_to_call)
    vec_call = builder.load(vec_call)
    vec_call = builder.ptr_cast(vec_call, code_type.get_vector_call_func(visitor.get_code_gen()).get_ptr_to())

    # Allocate memory for the args on the stack so it's much faster
    args_stack_memory = visitor.generate_entry_block_var(
        code_type.get_array_of(code_type.get_py_obj_ptr(code_gen), len(args) + 1))

    # Set the args into the stack memory
    for i, e in enumerate(args):
        arg_gep = builder.gep(args_stack_memory, builder.const_int32(0), builder.const_int32(i))
        builder.store(e, arg_gep)

    # Cast the stack memory to simplify the type
    args_stack_memory = builder.ptr_cast(args_stack_memory, code_type.get_py_obj_ptr(code_gen).get_ptr_to())

    vec_args = [func_to_call, args_stack_memory, builder.const_int64(len(args)),
                builder.const_null(code_type.get_py_obj_ptr(code_gen))]

    return builder.call_ptr(vec_call, vec_args)


def call_py_func_tp_call(visitor, func_to_call, args):
    """
    Call a python function using the tp_call convention
    """
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    call_funcs_args = [code_type.get_py_obj_ptr(visitor.get_code_gen())] * 3
    arg_list = tuple_call.python_tuple_new(code_gen, builder, builder.const_int64(len(args)))
    for i, e in enumerate(args):
        tuple_call.python_tuple_set_unsafe(code_gen, builder, arg_list, builder.const_int64(i), e)
    kwargs = tuple_call.python_tuple_new(code_gen, builder, builder.const_int64(0))

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
    gep_indices = [visitor.get_builder().const_int32(0), visitor.get_builder().const_int32(20)]
    return visitor.get_builder().gep2(func_type, visitor.get_code_gen().get_python_type().to_code_type(),
                                      gep_indices)

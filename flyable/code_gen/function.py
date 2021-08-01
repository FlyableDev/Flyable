import flyable.code_gen.fly_obj as fly_obj
import flyable.code_gen.exception as excp
import flyable.code_gen.code_type as code_type


def check_py_obj_is_func_type(visitor, func_to_call):
    obj_type = fly_obj.get_py_obj_type(visitor.get_builder(), func_to_call)
    func_type = visitor.get_builder().global_var(visitor.get_code_gen().get_py_func_type())
    return visitor.get_builder().eq(obj_type, func_type)


def call_py_func(visitor, func_to_call, args):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()
    valid_type_block = visitor.get_builder().create_block()
    invalid_type_block = visitor.get_builder().create_block()
    is_func = check_py_obj_is_func_type(visitor, func_to_call)

    visitor.get_builder().cond_br(is_func, valid_type_block, invalid_type_block)

    builder.set_insert_block(valid_type_block)
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


    result = builder.call_ptr(vec_call, vec_args)

    builder.set_insert_block(invalid_type_block)
    excp.raise_callable_error(visitor)
    excp.handle_raised_excp(visitor)

    builder.set_insert_block(valid_type_block)

    return result


def py_obj_func_get_vectorcall_ptr(visitor, func):
    func = visitor.get_builder().ptr_cast(func, visitor.get_code_gen().get_py_func_struct().to_code_type().get_ptr_to())
    gep_indices = [visitor.get_builder().const_int32(0), visitor.get_builder().const_int32(14)]
    return visitor.get_builder().gep2(func, visitor.get_code_gen().get_py_func_struct().to_code_type(), gep_indices)

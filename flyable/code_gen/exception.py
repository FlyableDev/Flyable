"""
Modules to handle Python exception
"""
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen


def py_runtime_print_error(code_gen, builder):
    print_error_func = code_gen.get_or_create_func("PyErr_Print", code_type.get_void(), [], gen.Linkage.EXTERNAL)
    return builder.call(print_error_func, [])


def py_runtime_clear_error(code_gen, builder):
    clear_error_func = code_gen.get_or_create_func("PyErr_Clear", code_type.get_void(), [], gen.Linkage.EXTERNAL)
    return builder.call(clear_error_func, [])


def py_runtime_set_excp(visitor, type, value):
    args_type = [code_type.get_py_obj_ptr(visitor.get_code_gen())] * 2
    set_error_func = visitor.get_code_gen().get_or_create_func("PyErr_SetObject", code_type.get_void())
    return visitor.get_builder().call(set_error_func, [type, value])


def py_runtime_get_excp(code_gen, builder):
    get_excp_func = code_gen.get_or_create_func("PyErr_Occurred", code_type.get_py_obj_ptr(code_gen), [],
                                                gen.Linkage.EXTERNAL)
    return builder.call(get_excp_func, [])


def raise_exception(visitor, type, value):
    py_runtime_set_excp(visitor, type, value)


def raise_index_error(visitor):
    raise_func = visitor.get_code_gen().get_or_create_func("flyable_raise_index_error", code_type.get_void(), [],
                                                           gen.Linkage.EXTERNAL)
    visitor.get_builder().call(raise_func, [])


def raise_callable_error(visitor):
    raise_func = visitor.get_code_gen().get_or_create_func("flyable_raise_callable_error", code_type.get_void(), [],
                                                           gen.Linkage.EXTERNAL)
    visitor.get_builder().call(raise_func, [])


def raise_assert_error(visitor, obj):
    args_type = [code_type.get_py_obj_ptr(visitor.get_code_gen())]
    raise_func = visitor.get_code_gen().get_or_create_func("flyable_raise_assert_error", code_type.get_void(),
                                                           args_type, gen.Linkage.EXTERNAL)
    visitor.get_builder().call(raise_func, [obj])


def check_excp(visitor, value_to_check):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()
    no_excp_block = builder.create_block()
    excp_block = builder.create_block()

    has_excp = builder.eq(value_to_check, builder.const_null(code_type.get_py_obj_ptr(code_gen)))

    # If the value is null, it means there is an exception
    builder.cond_br(has_excp, excp_block, no_excp_block)

    builder.set_insert_block(excp_block)
    handle_raised_excp(visitor)

    builder.set_insert_block(no_excp_block)


def handle_raised_excp(visitor):
    found_block = visitor.get_except_block()
    if found_block is None:
        func_type = visitor.get_func().get_return_type()
        visitor.get_builder().ret_null()
    else:
        visitor.get_builder().br(found_block)

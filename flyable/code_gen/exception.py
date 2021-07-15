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

from flyable.code_gen.code_type import CodeType
from flyable.code_gen.code_gen import CodeFunc
import flyable.code_gen.code_type as code_type

"""
Module to call runtimes fonctions
"""


def create_unicode(code_gen, builder, str):
    """
    Generate an external call to the python function to create a string
    """
    from_string = code_gen.get_or_create_func("PyUnicode_FromString", CodeType(CodeType.CodePrimitive.INT8).get_ptr_to()
    [CodeType(CodeType.CodePrimitive.INT8).get_ptr_to()])
    return builder.call(from_string, [str])


def malloc_call(code_gen, builder, value_size):
    """
    Generate an external call to the Python runtime memory allocator
    """

    from flyable.code_gen.code_gen import CodeFunc

    malloc_func = code_gen.get_or_create_func("PyMem_Malloc", CodeType(CodeType.CodePrimitive.INT8).get_ptr_to(),
                                              [CodeType(CodeType.CodePrimitive.INT64)], CodeFunc.Linkage.EXTERNAL)
    return builder.call(malloc_func, [value_size])


def is_true(value):
    pass


def is_false(value):
    pass


def py_runtime_init(code_gen, builder):
    init_func = code_gen.get_or_create_func("Py_Initialize", code_type.get_void(), [], CodeFunc.Linkage.EXTERNAL)
    return builder.call(init_func, [])


def py_runtime_object_print(code_gen, builder, obj):
    print_func = code_gen.get_or_create_func("PyObject_Print", code_type.get_int32(),
                                             [code_type.get_int8_ptr(), code_type.get_int8_ptr(),
                                              code_type.get_int32()], CodeFunc.Linkage.EXTERNAL)
    flag = builder.const_int32(1)  # Print Flag only support Py_PRINT_RAW that is defined as 1

    return builder.call(print_func, [obj, builder.const_null(code_type.get_int8_ptr()), flag])


def py_runtime_ImportModule(code_gen, builder, name):
    imp_func = code_gen.get_or_create_func("PyImport_ImportModule",
                                           CodeType(CodeType.CodePrimitive.INT8).get_ptr_to(),
                                           [CodeType(CodeType.CodePrimitive.INT8).get_ptr_to()],
                                           CodeFunc.Linkage.EXTERNAL)
    return builder.call(imp_func, [name_c_str])


def value_to_pyobj(code_gen, builder, value, lang_type):
    if lang_type.is_int():
        py_func = code_gen.get_or_create_func("PyLong_FromLongLong", code_type.get_int8_ptr(),
                                              [CodeType(CodeType.CodePrimitive.INT64)], CodeFunc.Linkage.EXTERNAL)
        return builder.call(py_func, [value])
    elif lang_type.is_dec():
        py_func = code_gen.get_or_create_func("PyFloat_FromDouble",
                                              CodeType(CodeType.CodePrimitive.INT8).get_ptr_to()
                                              [CodeType(CodeType.CodePrimitive.DOUBLE)])
        return builder.call(py_func, [value])
    elif lang_type.is_obj():
        return value

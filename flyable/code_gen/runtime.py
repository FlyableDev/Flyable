from flyable.code_gen.code_type import CodeType
from flyable.code_gen.code_gen import CodeFunc
import flyable.code_gen.code_type as code_type
from flyable.code_gen.code_gen import *
import flyable.data.type_hint as type_hint
import flyable.code_gen.debug as debug

"""
Module to call runtimes functions
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
    malloc_func = code_gen.get_or_create_func("PyMem_Malloc", code_type.get_py_obj_ptr(code_gen),
                                              [CodeType(CodeType.CodePrimitive.INT64)], Linkage.EXTERNAL)
    return builder.call(malloc_func, [value_size])


def free_call(code_gen, builder, memory_to_free):
    free_func = code_gen.get_or_create_func("PyMem_Free", code_type.get_void(), [code_type.get_int8_ptr()],
                                            Linkage.EXTERNAL)
    memory_to_free = builder.ptr_cast(memory_to_free, code_type.get_int8_ptr())
    return builder.call(free_func, [memory_to_free])


def py_runtime_get_string(code_gen, builder, value):
    str_ptr = builder.ptr_cast(builder.global_str(value), code_type.get_int8_ptr())
    args_type = [code_type.get_int8_ptr(), code_type.get_int64()]
    new_str_func = code_gen.get_or_create_func("PyUnicode_FromStringAndSize", code_type.get_py_obj_ptr(code_gen),
                                               args_type, Linkage.EXTERNAL)
    return builder.call(new_str_func, [str_ptr, builder.const_int64(len(value))])


def py_runtime_init(code_gen, builder):
    init_func = code_gen.get_or_create_func("Py_Initialize", code_type.get_void(), [], Linkage.EXTERNAL)
    return builder.call(init_func, [])


def py_runtime_object_print(code_gen, builder, obj):
    print_func = code_gen.get_or_create_func("__flyable__print", code_type.get_int32(),
                                             [code_type.get_py_obj_ptr(code_gen)], Linkage.EXTERNAL)
    return builder.call(print_func, [obj])

def value_to_pyobj(code_gen, builder, value, value_type):
    result_type = lang_type.get_python_obj_type()

    if value_type.is_int():

        int_const_hint = type_hint.get_lang_type_contained_hint_type(value_type, type_hint.TypeHintConstInt)

        if int_const_hint is None:
            py_func = code_gen.get_or_create_func("PyLong_FromLongLong", code_type.get_py_obj_ptr(code_gen),
                                                  [CodeType(CodeType.CodePrimitive.INT64)], Linkage.EXTERNAL)
            result_type.add_hint(type_hint.TypeHintRefIncr())
            return result_type, builder.call(py_func, [value])
        else:
            return result_type, builder.load(
                builder.global_var(code_gen.get_or_insert_const(int_const_hint.get_value())))
    elif value_type.is_dec():
        dec_const_hint = type_hint.get_lang_type_contained_hint_type(value_type, type_hint.TypeHintConstDec)
        if dec_const_hint is None:
            result_type.add_hint(type_hint.TypeHintRefIncr())
            py_func = code_gen.get_or_create_func("PyFloat_FromDouble", code_type.get_py_obj_ptr(code_gen),
                                                  [code_type.get_double()], Linkage.EXTERNAL)
            return result_type, builder.call(py_func, [value])
        else:
            return result_type, builder.load(
                builder.global_var(code_gen.get_or_insert_const(dec_const_hint.get_value())))
    elif value_type.is_bool():
        # TODO : Directly use the global var to avoid the func call
        py_func = code_gen.get_or_create_func("PyBool_FromLong", code_type.get_py_obj_ptr(code_gen),
                                              [code_type.get_int1()], Linkage.EXTERNAL)
        result_type.add_hint(type_hint.TypeHintRefIncr())
        return result_type, builder.call(py_func, [value])
    elif value_type.is_obj() or value_type.is_collection():
        # Make sure the object is of python objet ptr to keep consistent types
        if type_hint.is_incremented_type(value_type):  # Keep the incremental hint
            result_type.add_hint(type_hint.TypeHintRefIncr())
        return result_type, builder.ptr_cast(value, code_type.get_py_obj_ptr(code_gen))
    elif value_type.is_none():
        none_value = builder.load(builder.global_var(code_gen.get_none()))
        return result_type, none_value

    return result_type, value


def py_runtime_obj_len(code_gen, builder, value):
    func_name = "PyObject_Length"
    py_func = code_gen.get_or_create_func(func_name, code_type.get_int64(), [code_type.get_py_obj_ptr(code_gen)],
                                          Linkage.EXTERNAL)
    return builder.call(py_func, [value])

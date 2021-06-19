import flyable.code_gen.code_gen
import flyable.code_gen.code_type as code_type


def py_object_is_type(code_gen, builder, type, value, value_to_be):
    func = code_gen.get_or_create_func("PyObject_IsSubclass", code_type.get_int32(), [code_type.get_int8_ptr()],
                                       code_type.CodeFunc.Linkage.EXTERNAL)
    return builder.call(func, [value, value_to_be])

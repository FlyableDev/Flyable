import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen


def python_dict_new(code_gen, builder):
    func = code_gen.get_or_create_func("PyDict_New", code_type.get_int8_ptr(), [], gen.Linkage.EXTERNAL)
    return builder.call(func, [])


def python_dict_set_item(code_gen, builder, dict, key, value):
    func = code_gen.get_or_create_func("PyDict_SetItem", code_type.get_int32(),
                                       [code_type.get_int8_ptr()] * 3, gen.Linkage.EXTERNAL)
    return builder.call(func, [dict, key, value])

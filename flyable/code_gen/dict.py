import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen


def python_dict_new(visitor):
    builder, code_gen = visitor.get_builder(), visitor.get_code_gen()
    func = code_gen.get_or_create_func("PyDict_New", code_type.get_py_obj_ptr(code_gen), [], gen.Linkage.EXTERNAL)
    return builder.call(func, [])


def python_dict_set_item(visitor, dict, key, value):
    builder, code_gen = visitor.get_builder(), visitor.get_code_gen()
    func = code_gen.get_or_create_func("PyDict_SetItem", code_type.get_int32(),
                                       [code_type.get_py_obj_ptr(code_gen)] * 3, gen.Linkage.EXTERNAL)
    return builder.call(func, [dict, key, value])


def python_dict_len(visitor, dict):
    builder, code_gen = visitor.get_builder(), visitor.get_code_gen()
    args_types = [code_type.get_py_obj_ptr(code_gen)]
    func = code_gen.get_or_create_func("PyDict_Size", code_type.get_int64(), args_types, gen.Linkage.EXTERNAL)
    return builder.call(func, [dict])

"""
Handle module
"""

import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen


def import_py_module(code_gen, builder, name):
    module_str = builder.global_str(name)
    builder.load(module_str)
    module_str = builder.ptr_cast(module_str, code_type.get_int8_ptr())

    func_args = [code_type.get_int8_ptr()]
    module_func = code_gen.get_or_create_func("PyImport_ImportModule", code_type.get_py_obj_ptr(code_gen), func_args,
                                              gen.Linkage.EXTERNAL)
    return builder.call(module_func, [module_str])

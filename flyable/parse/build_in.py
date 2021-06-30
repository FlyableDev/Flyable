"""
Module managing all functions
"""

import flyable.code_gen.runtime as runtime
import flyable.code_gen.code_type as code_type
import flyable.code_gen.list as gen_list
import flyable.data.lang_type as lang_type


class BuildInFunc:

    def __init__(self):
        pass

    def parse(self, args_types, args, codegen, builder):
        pass


class BuildInPrint(BuildInFunc):

    def __init__(self):
        super().__init__()

    def parse(self, args_types, args, codegen, builder):
        arg_type = args_types[0]
        obj_to_send = None
        if arg_type.is_int() or arg_type.is_dec() or arg_type.is_bool():
            obj_to_send = runtime.value_to_pyobj(codegen, builder, args[0], arg_type)
        elif arg_type.is_obj():
            obj_to_send = builder.ptr_cast(args[0], code_type.get_int8_ptr())
        else:
            obj_to_send = args[0]

        return lang_type.get_none_type(), runtime.py_runtime_object_print(codegen, builder, obj_to_send)


class BuildInList(BuildInFunc):

    def __init__(self):
        super().__init__()

    def parse(self, args_types, args, codegen, builder):
        if len(args_types) == 0:
            list_type = lang_type.get_list_of_python_obj_type()
            return list_type, gen_list.instanciate_pyton_list(codegen, builder, builder.const_int64(0))


class BuildInLen(BuildInFunc):

    def __init__(self):
        super().__init__()

    def parse(self, args_types, args, codegen, builder):
        return runtime.py_runtime_obj_len(codegen, builder, args[0])


def get_build_in(name):
    name = str(name)
    build_in_funcs = {
        "print": BuildInPrint,
        "list": BuildInList,
        "len": BuildInLen,
    }

    if name in build_in_funcs:
        return build_in_funcs[name]()  # Create an instance of the build-in class
    return None

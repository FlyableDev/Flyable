"""
Module routine to handle set
"""

from flyable.code_gen.code_type import CodeType
import flyable.code_gen.code_gen as gen
import flyable.code_gen.code_type as code_type


def instanciate_pyton_set(code_gen, builder, obj):
    """
    Generate the code to allocate a Python List
    """
    new_list_args_types = [code_type.get_int64()]
    new_list_func = code_gen.get_or_create_func("PySet_New", CodeType(CodeType.CodePrimitive.INT8).get_ptr_to(),
                                                new_list_args_types, gen.Linkage.EXTERNAL)
    return builder.call(new_list_func, [obj])


def python_set_add(code_gen, builder, set_obj, item):
    """
    Generate the code to set an element in a Python List
    """
    set_item_args_types = [code_type.get_int8_ptr(), code_type.get_int8_ptr()]
    set_item_func = code_gen.get_or_create_func("PySet_Add", code_type.get_int32(),
                                                set_item_args_types, gen.Linkage.EXTERNAL)
    return builder.call(set_item_func, [set_obj, item])


def python_set_len(code_gen, builder, set_obj):
    """
    Generate the code that returns the len of the list
    """
    args_types = [code_type.get_py_obj_ptr(code_gen)]
    list_len_func = code_gen.get_or_create_func("PySet_Size", code_type.get_int64(), args_types, gen.Linkage.EXTERNAL)
    return builder.call(list_len_func, [set_obj])

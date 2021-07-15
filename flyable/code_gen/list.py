"""
Module with routines to handle Python and Flyable list
"""

from flyable.code_gen.code_type import CodeType
import flyable.code_gen.code_gen as gen
import flyable.code_gen.code_type as code_type


def instanciate_pyton_list(code_gen, builder, len):
    """
    Generate the code to allocate a Python List
    """
    new_list_args_types = [code_type.get_int64()]
    new_list_func = code_gen.get_or_create_func("PyList_New", code_type.get_py_obj_ptr(code_gen),
                                                new_list_args_types, gen.Linkage.EXTERNAL)
    return builder.call(new_list_func, [len])


def python_list_set(code_gen, builder, list, index, item):
    """
    Generate the code to set an element in a Python List
    """
    set_item_args_types = [code_type.get_py_obj_ptr(code_gen), code_type.get_int64(),
                           code_type.get_py_obj_ptr(code_gen)]
    set_item_func = code_gen.get_or_create_func("PyList_SetItem", code_type.get_int32(),
                                                set_item_args_types, gen.Linkage.EXTERNAL)
    return builder.call(set_item_func, [list, index, item])


def python_list_append(code_gen, builder, list, item):
    """
    Generate the code to set an element in a Python List
    """
    set_item_args_types = [code_type.get_py_obj_ptr(code_gen), code_type.get_py_obj_ptr(code_gen)]
    set_item_func = code_gen.get_or_create_func("PyList_Append", code_type.get_int32(),
                                                set_item_args_types, gen.Linkage.EXTERNAL)
    return builder.call(set_item_func, [list, item])


def python_list_len(code_gen, builder, list):
    """
    Generate the code that returns the len of the list
    """
    args_types = [code_type.get_py_obj_ptr(code_gen)]
    list_len_func = code_gen.get_or_create_func("PyList_Size", code_type.get_int64(), args_types, gen.Linkage.EXTERNAL)
    return builder.call(list_len_func, [list])

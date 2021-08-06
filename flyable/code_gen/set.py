"""
Module routine to handle set
"""

from flyable.code_gen.code_type import CodeType
import flyable.code_gen.code_gen as gen
import flyable.code_gen.code_type as code_type


def instanciate_python_set(visitor, obj):
    """
    Generate the code to allocate a Python List
    """
    builder = visitor.get_builder()
    code_gen = visitor.get_code_gen()
    new_list_args_types = [code_type.get_py_obj_ptr(code_gen)]
    new_list_func = code_gen.get_or_create_func("PySet_New", code_type.get_py_obj_ptr(code_gen),
                                                new_list_args_types, gen.Linkage.EXTERNAL)
    return builder.call(new_list_func, [obj])


def python_set_add(visitor, set_obj, item):
    """
    Generate the code to set an element in a Python List
    """
    builder = visitor.get_builder()
    code_gen = visitor.get_code_gen()
    set_item_args_types = [code_type.get_py_obj_ptr(code_gen), code_type.get_py_obj_ptr(code_gen)]
    set_item_func = code_gen.get_or_create_func("PySet_Add", code_type.get_int32(),
                                                set_item_args_types, gen.Linkage.EXTERNAL)
    return builder.call(set_item_func, [set_obj, item])


def python_set_len(visitor, set_obj):
    """
    Generate the code that returns the len of the list
    """
    builder = visitor.get_builder()
    code_gen = visitor.get_code_gen()
    args_types = [code_type.get_py_obj_ptr(code_gen)]
    list_len_func = code_gen.get_or_create_func("PySet_Size", code_type.get_int64(), args_types, gen.Linkage.EXTERNAL)
    return builder.call(list_len_func, [set_obj])

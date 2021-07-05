"""
Module for Python tuple related functions
"""

from flyable.code_gen.code_type import CodeType
import flyable.code_gen.code_gen as gen
import flyable.code_gen.code_type as code_type


def python_tuple_new(code_gen, builder, size):
    """
    Generate the code to allocate a Python Tuple
    """
    new_list_args_types = [code_type.get_int64()]
    new_list_func = code_gen.get_or_create_func("PyTuple_New", code_type.get_py_obj_ptr(code_gen),
                                                new_list_args_types, gen.Linkage.EXTERNAL)
    return builder.call(new_list_func, [size])


def python_tuple_set(code_gen, builder, list, index, item):
    """
    Generate the code to set an element in a Python Tuple
    """
    set_item_args_types = [code_type.get_py_obj_ptr(code_gen), code_type.get_int64(),
                           code_type.get_py_obj_ptr(code_gen)]
    set_item_func = code_gen.get_or_create_func("PyTuple_SetItem", code_type.get_int32(),
                                                set_item_args_types, gen.Linkage.EXTERNAL)
    return builder.call(set_item_func, [list, index, item])


def python_tuple_set_unsafe(code_gen, builder, list, index, item):
    """
    Generate the code to set an element in a Python Tuple.
    Should only be used for filling new tuples.
    """

    # TODO : PyTuple_SetItem is slow because it does a lot of checks, find a direct way inlinable to set the data

    set_item_args_types = [code_type.get_py_obj_ptr(code_gen), code_type.get_int64(),
                           code_type.get_py_obj_ptr(code_gen)]
    set_item_func = code_gen.get_or_create_func("PyTuple_SetItem", code_type.get_int32(), set_item_args_types,
                                                gen.Linkage.EXTERNAL)
    return builder.call(set_item_func, [list, index, item])

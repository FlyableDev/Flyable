import flyable.code_gen.type as _type
import flyable.code_gen.fly_obj as fly_obj

"""
Module related to the code generation of the protocol
"""


def is_iter_func_name(name):
    return name == "__next__"


def call_iter_next(visitor, obj, args):
    builder = visitor.get_builder()
    obj_type = fly_obj.get_py_obj_type(visitor.get_builder(), obj)
    obj_type.py_object_type_get_iter_next(visitor, obj_type)


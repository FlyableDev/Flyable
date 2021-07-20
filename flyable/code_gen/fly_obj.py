"""
module to handle flyable object info
"""


def get_obj_attribute_start_index():
    """
    Return the gep index for flyable object attribute
    """
    return 2


def get_py_obj_type_ptr(builder, obj):
    return builder.gep(obj, builder.const_int32(0), builder.const_int32(1))


def get_py_obj_type(builder, obj):
    return builder.load(get_py_obj_type_ptr(builder, obj))

"""
Module with the functions related to code generation of code managing the reference counter
"""


def get_ref_counter_ptr(visitor, value_type, value):
    """
    Generate the code to get the ref counter address of an object
    """
    builder = visitor.get_builder()
    if not value_type.is_primitive() and not value_type.is_none():
        zero = builder.const_int32(0)
        gep = builder.const_int32(2)
        return builder.gep(value, zero, gep)
    return None


def ref_incr(visitor, value_type, value):
    """
    Generate the code to increment the reference counter by one
    """
    builder = visitor.get_builder()
    ref_ptr = get_ref_counter_ptr(visitor, value_type, value)
    if ref_ptr is not None:
        ref_count = builder.load(ref_ptr)
        ref_count = builder.add(ref_count, builder.const_int64(1))
        builder.store(ref_count, ref_ptr)


def ref_decr(visitor, value_type, value):
    pass


def ref_decr_nullable(visitor, value_type, value):
    pass

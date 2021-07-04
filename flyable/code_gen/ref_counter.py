"""
Module with the functions related to code generation of code managing the reference counter
"""


def get_ref_counter_ptr(code_gen, builder, value_type, value):
    """
    Generate the code to get the ref counter address of an object
    """
    if not value_type.is_primitive():
        return builder.gep(value,0)
    return None


def ref_incr(code_gen, builder, value_type, value):
    """
    Generate the code to increment the reference counter by one
    """
    ref_ptr = get_ref_counter_ptr(code_gen, builder, value_type, value)
    if ref_ptr is not None:
        ref_count = builder.load(ref_ptr)
        ref_count = builder.add(ref_count, builder.const_int64(1))
        builder.store(ref_count, ref_ptr)


def ref_decr(code_gen, builder, value_type, value):
    pass


def ref_decr_nullable(code_gen, builder, value_type, value):
    pass

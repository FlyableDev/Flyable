"""
Module with the functions related to code generation of code managing the reference counter
"""
import flyable.data.lang_type as lang_type
import flyable.code_gen.fly_obj as fly_obj
import flyable.code_gen.type as gen_type
import flyable.code_gen.code_type as code_type
import flyable.data.type_hint as hint
import flyable.code_gen.debug as debug
import flyable.code_gen.exception as excp


def get_ref_counter_ptr(visitor, value_type, value):
    """
    Generate the code to get the ref counter address of an object
    """
    builder = visitor.get_builder()
    if not value_type.is_primitive() and not value_type.is_none():
        zero = builder.const_int32(0)
        gep = builder.const_int32(0)
        return builder.gep(value, zero, gep)
    return None


def get_ref_count(visitor, value):
    return visitor.get_builder().load(get_ref_counter_ptr(visitor, lang_type.get_python_obj_type(), value))


def set_ref_count(visitor, obj, value):
    visitor.get_builder().store(value, get_ref_counter_ptr(visitor, lang_type.get_python_obj_type(), obj))


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
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    ref_ptr = get_ref_counter_ptr(visitor, value_type, value)
    if ref_ptr is not None:
        dealloc_block = builder.create_block()
        continue_block = builder.create_block()
        ref_count = builder.load(ref_ptr)
        need_to_dealloc = builder.eq(ref_count, builder.const_int64(1))
        builder.cond_br(need_to_dealloc, dealloc_block, continue_block)

        builder.set_insert_block(dealloc_block)
        obj_type = fly_obj.get_py_obj_type(visitor.get_builder(), value)
        dealloc_ptr = gen_type.py_object_type_get_dealloc_ptr(visitor, obj_type)
        dealloc_type = code_type.get_func(code_type.get_void(),
                                          [code_type.get_py_obj_ptr(code_gen)]).get_ptr_to().get_ptr_to()
        dealloc_ptr = builder.ptr_cast(dealloc_ptr, dealloc_type)
        dealloc_ptr = builder.load(dealloc_ptr)
        builder.call_ptr(dealloc_ptr, [value])
        builder.br(continue_block)
        builder.set_insert_block(continue_block)


def ref_decr_nullable(visitor, value_type, value):
    pass


def ref_decr_multiple(visitor, types, values):
    for i, value in enumerate(values):
        ref_decr(visitor, types[i], values[i])


def ref_decr_multiple_incr(visitor, types, values):
    for i, value in enumerate(values):
        if hint.is_incremented_type(types[i]):
            ref_decr(visitor, types[i], values[i])

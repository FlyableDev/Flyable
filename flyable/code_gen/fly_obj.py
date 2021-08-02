import flyable.code_gen.runtime as runtime
import flyable.code_gen.ref_counter as ref_counter
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen

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


def allocate_flyable_instance(visitor, lang_class):
    lang_type = lang_class.get_lang_type()
    ptr_type = lang_type.to_code_type(visitor.get_code_gen())
    alloc_size = visitor.get_builder().size_of_type_ptr_element(ptr_type)
    value = runtime.malloc_call(visitor.get_code_gen(), visitor.get_builder(), alloc_size)
    value = visitor.get_builder().ptr_cast(value, ptr_type)

    # Set the ref counter to 0
    ref_ptr = ref_counter.get_ref_counter_ptr(visitor, lang_type, value)
    visitor.get_builder().store(visitor.get_builder().const_int64(100), ref_ptr)

    # Set the type of
    type_ptr = get_py_obj_type_ptr(visitor.get_builder(), value)
    none_value = visitor.get_builder().global_var(visitor.get_code_gen().get_none())
    none_value = visitor.get_builder().load(none_value)
    visitor.get_builder().store(none_value, type_ptr)

    return value

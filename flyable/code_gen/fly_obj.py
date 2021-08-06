import flyable.code_gen.runtime as runtime
import flyable.code_gen.ref_counter as ref_counter
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen

"""
module to handle flyable object info
"""


def py_obj_get_attr(visitor, obj, name):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    # get attr : replicate https://github.com/python/cpython/blob/main/Objects/object.c#L903
    # First need to call get_attro, then the get_attr if get_attro is null

    """"
    attr_found_var = visitor.generate_entry_block_var(code_type.get_py_obj_ptr(code_gen))

    get_attro_block = builder.create_block()
    get_attr_block = builder.create_block()
    continue_block = builder.create_block()

    # Get the function first
    obj_type = get_py_obj_type(visitor.get_builder(), obj)
    obj_type = builder.ptr_cast(obj_type, code_gen.get_python_type().to_code_type().get_ptr_to())

    get_attro = get_py_obj_type_getattro_ptr(visitor, obj_type)
    get_attro = builder.load(get_attro)

    null_get_attr = builder.const_null(code_type.get_int8_ptr())
    is_attr_null = builder.eq(null_get_attr, get_attro)

    builder.cond_br(is_attr_null, get_attr_block, get_attro_block)

    builder.set_insert_block(get_attro_block)
    get_attro_type = code_type.get_func(code_type.get_py_obj_ptr(code_gen),
                                        [code_type.get_py_obj_ptr(code_gen)] * 2).get_ptr_to()
    get_attro_func = builder.ptr_cast(get_attro, get_attro_type)
    attribute_py_str = builder.global_var(code_gen.get_or_insert_str(name))
    attribute_py_str = builder.load(attribute_py_str)
    found_attro = builder.call_ptr(get_attro_func, [obj, attribute_py_str])
    builder.store(found_attro, attr_found_var)
    builder.br(continue_block)

    builder.set_insert_block(get_attr_block)
    get_attr = get_py_obj_type_getattr_ptr(visitor, obj_type)
    get_attr = builder.load(get_attr)
    get_attr_type = code_type.get_func(code_type.get_py_obj_ptr(code_gen),
                                       [code_type.get_py_obj_ptr(code_gen), code_type.get_int8_ptr()]).get_ptr_to()
    get_attr_func = builder.ptr_cast(get_attr, get_attr_type)
    str_attr = builder.ptr_cast(builder.global_str(name), code_type.get_int8_ptr())
    found_attr = builder.call_ptr(get_attr_func, [obj, str_attr])
    builder.store(found_attr, attr_found_var)
    builder.br(continue_block)

    builder.set_insert_block(continue_block)
    return builder.load(attr_found_var)
    """

    attribute_py_str = builder.global_var(code_gen.get_or_insert_str(name))
    attribute_py_str = builder.load(attribute_py_str)
    func_get = code_gen.get_or_create_func("PyObject_GetAttr", code_type.get_py_obj_ptr(code_gen),
                                           [code_type.get_py_obj_ptr(code_gen)] * 2, gen.Linkage.EXTERNAL)

    return builder.call(func_get, [obj, attribute_py_str])


def get_obj_attribute_start_index():
    """
    Return the gep index for flyable object attribute
    """
    return 2


def get_py_obj_type_ptr(builder, obj):
    return builder.gep(obj, builder.const_int32(0), builder.const_int32(1))


def get_py_obj_type(builder, obj):
    return builder.load(get_py_obj_type_ptr(builder, obj))


def get_py_obj_type_getattr_ptr(visitor, obj):
    builder = visitor.get_builder()
    return visitor.get_builder().gep(obj, builder.const_int32(0), builder.const_int32(7))


def get_py_obj_type_getattro_ptr(visitor, obj):
    builder = visitor.get_builder()
    return visitor.get_builder().gep(obj, builder.const_int32(0), builder.const_int32(17))


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

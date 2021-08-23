"""
Module with the functions related to code generation of code managing the reference counter
"""
import flyable.data.lang_type as lang_type
import flyable.code_gen.fly_obj as fly_obj
import flyable.code_gen.type as gen_type
import flyable.code_gen.code_type as code_type
import flyable.data.type_hint as hint
import flyable.code_gen.caller as caller
import flyable.code_gen.runtime as runtime
import flyable.code_gen.debug as debug
import flyable.code_gen.exception as excp


def is_ref_counting_type(value_type):
    return not value_type.is_primitive() and not value_type.is_none()


def get_ref_counter_ptr(visitor, value_type, value):
    """
    Generate the code to get the ref counter address of an object
    """
    builder = visitor.get_builder()
    if is_ref_counting_type(value_type):
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
    if is_ref_counting_type(value_type):
        ref_ptr = get_ref_counter_ptr(visitor, value_type, value)
        ref_count = builder.load(ref_ptr)
        ref_count = builder.add(ref_count, builder.const_int64(1))
        builder.store(ref_count, ref_ptr)


def ref_decr(visitor, value_type, value):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    if is_ref_counting_type(value_type):
        ref_ptr = get_ref_counter_ptr(visitor, value_type, value)
        ref_count = builder.load(ref_ptr)

        dealloc_block = builder.create_block()
        decrement_block = builder.create_block()

        need_to_dealloc = builder.eq(ref_count, builder.const_int64(1))
        builder.cond_br(need_to_dealloc, dealloc_block, decrement_block)

        builder.set_insert_block(dealloc_block)
        if value_type.is_obj():
            caller.call_obj(visitor, "__del__", value, value_type, [], [], True)
            runtime.free_call(code_gen, builder, value)
        elif value_type.is_python_obj() or value_type.is_collection():
            obj_type = fly_obj.get_py_obj_type(visitor.get_builder(), value)
            dealloc_ptr = gen_type.py_object_type_get_dealloc_ptr(visitor, obj_type)
            dealloc_type = code_type.get_func(code_type.get_void(),
                                              [code_type.get_py_obj_ptr(code_gen)]).get_ptr_to().get_ptr_to()
            dealloc_ptr = builder.ptr_cast(dealloc_ptr, dealloc_type)
            dealloc_ptr = builder.load(dealloc_ptr)
            builder.call_ptr(dealloc_ptr, [value])

        continue_block = builder.create_block()

        builder.br(continue_block)

        builder.set_insert_block(decrement_block)
        new_ref_count = builder.sub(ref_count, builder.const_int64(1))
        builder.store(new_ref_count, ref_ptr)
        builder.br(continue_block)

        builder.set_insert_block(continue_block)


def ref_decr_nullable(visitor, value_type, value):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    if is_ref_counting_type(value_type):
        not_null_block = builder.create_block()
        continue_block = builder.create_block()

        is_null = builder.eq(value, builder.const_null(value_type.to_code_type(code_gen)))
        builder.cond_br(is_null, continue_block, not_null_block)

        builder.set_insert_block(not_null_block)
        ref_decr(visitor, value_type, value)
        builder.br(continue_block)

        builder.set_insert_block(continue_block)


def ref_decr_multiple(visitor, types, values):
    for i, value in enumerate(values):
        ref_decr(visitor, types[i], values[i])


def ref_decr_multiple_incr(visitor, types, values):
    for i, value in enumerate(values):
        if hint.is_incremented_type(types[i]):
            ref_decr(visitor, types[i], values[i])


def ref_decr_incr(visitor, type, value):
    if hint.is_incremented_type(type):
        ref_decr(visitor, type, value)


def decr_all_variables(visitor):
    for var in visitor.get_func().get_context().vars_iter():
        if not var.is_arg():
            if var.is_global():
                value = visitor.get_builder().global_var(var.get_code_gen_value())
            else:
                value = var.get_code_gen_value()
            value = visitor.get_builder().load(value)
            ref_decr_nullable(visitor, var.get_type(), value)

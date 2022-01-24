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
import flyable.code_gen.list as _list
import flyable.code_gen.code_builder as code_builder
import flyable.code_gen.debug as debug
import flyable.code_gen.exception as excp
from flyable.parse.parser import ParserVisitor


def is_ref_counting_type(value_type: lang_type.LangType):
    return not value_type.is_primitive() and not value_type.is_none() and not value_type.is_unknown()


def get_ref_counter_ptr(builder: code_builder.CodeBuilder, value_type: lang_type.LangType, value: int):
    """
    Generate the code to get the ref counter address of an object
    """
    if is_ref_counting_type(value_type):
        zero = builder.const_int32(0)
        gep = builder.const_int32(0)
        return builder.gep(value, zero, gep)
    return None


def get_ref_count(builder: code_builder.CodeBuilder, value: int):
    ptr = get_ref_counter_ptr(builder, lang_type.get_python_obj_type(), value)
    if ptr is not None:
        return builder.load(ptr)


def set_ref_count(builder: code_builder.CodeBuilder, obj, value: int):
    print("HERE")
    ptr = get_ref_counter_ptr(builder, lang_type.get_python_obj_type(), obj)
    if ptr is not None:
        return builder.store(value, ptr)


def ref_incr(builder: code_builder.CodeBuilder, value_type, value):
    """
    Generate the code to increment the reference counter by one
    """
    if is_ref_counting_type(value_type):
        ref_ptr = get_ref_counter_ptr(builder, value_type, value)
        ref_count = builder.load(ref_ptr)
        ref_count = builder.add(ref_count, builder.const_int64(1))
        builder.store(ref_count, ref_ptr)


def ref_decr(visitor: ParserVisitor, value_type: lang_type.LangType, value):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    if is_ref_counting_type(value_type):
        ref_ptr = get_ref_counter_ptr(builder, value_type, value)
        ref_count = builder.load(ref_ptr)

        dealloc_block = builder.create_block()
        decrement_block = builder.create_block()

        need_to_dealloc = builder.eq(ref_count, builder.const_int64(1))
        builder.cond_br(need_to_dealloc, dealloc_block, decrement_block)

        builder.set_insert_block(dealloc_block)
        if value_type.is_obj():
            caller.call_obj(visitor, "__del__", value, value_type, [], [], True)
            runtime.free_call(code_gen, builder, value)
        elif value_type.is_list() or value_type.is_tuple():
            # Might be a bit slow to rely on dealloc call when we know that it's a list...
            obj_type = fly_obj.get_py_obj_type(visitor.get_builder(), value)
            dealloc_ptr = gen_type.py_object_type_get_dealloc_ptr(visitor, obj_type)
            dealloc_type = code_type.get_func(code_type.get_void(),
                                              [code_type.get_py_obj_ptr(code_gen)]).get_ptr_to().get_ptr_to()
            dealloc_ptr = builder.ptr_cast(dealloc_ptr, dealloc_type)
            dealloc_ptr = builder.load(dealloc_ptr)
            builder.call_ptr(dealloc_ptr, [value])

            """
            index_ptr = visitor.create_entry_alloca()
            content_ptr = _list.python_list_get_content_ptr(visitor, value)
            builder.store(builder.const_int32(0), index_ptr)

            cond_check_block = builder.create_block()
            array_size = _list.python_list_len(visitor, value)
            can_delete = builder.lt(builder.load(index_ptr), array_size)

            decrement_block = builder.create_block()
            continue_block = builder.create_block()

            builder.cond_br(can_delete, decrement_block, continue_block)

            builder.set_insert_block(decrement_block)
            
            # Decrement the content
            ref_decr(visitor, value_type.get_content(), builder.load(builder.gep(content_ptr, builder.load(index_ptr))))
            
            builder.br(continue_block)

            builder.set_insert_block(continue_block)
            """
        elif value_type.is_python_obj() or value_type.is_dict():
            obj_type = fly_obj.get_py_obj_type(visitor.get_builder(), value)
            dealloc_ptr = gen_type.py_object_type_get_dealloc_ptr(visitor, obj_type)
            dealloc_type = code_type.get_func(code_type.get_void(),
                                              [code_type.get_py_obj_ptr(code_gen)]).get_ptr_to().get_ptr_to()
            dealloc_ptr = builder.ptr_cast(dealloc_ptr, dealloc_type)
            dealloc_ptr = builder.load(dealloc_ptr)
            builder.call_ptr(dealloc_ptr, [value])
        else:
            raise Exception("Type " + str(value_type) + " unsupported to decrement the ref counter")

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
        if var.get_code_gen_value() is not None:
            if not var.is_arg():
                if var.is_global():
                    value = visitor.get_builder().global_var(var.get_code_gen_value())
                else:
                    value = var.get_code_gen_value()

                value = visitor.get_builder().load(value)
                ref_decr_nullable(visitor, var.get_type(), value)

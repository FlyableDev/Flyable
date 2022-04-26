import flyable.code_gen.type as _type
import flyable.code_gen.code_type as code_type
import flyable.code_gen.fly_obj as fly_obj
import flyable.code_gen.caller as caller
import flyable.data.lang_type as lang_type

"""
Module related to the code generation of the iter / next protocol
"""


def is_iter_func_name(name: str):
    return name == "__next__" or name == "__iter__"


def call_iter_protocol(visitor, name: str, obj: int):
    if name == "__next__":
        return call_iter_next(visitor, obj)
    elif name == "__iter__":
        return call_iter_iter(visitor, obj)
    raise Exception("Func with name" + name + " not supported for iterator protocol")


def call_iter_next(visitor, obj: int):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    result = visitor.generate_entry_block_var(code_type.get_py_obj_ptr(code_gen))

    iter_next_type = code_type.get_func(code_type.get_py_obj_ptr(code_gen), [code_type.get_py_obj_ptr(code_gen)])
    iter_next_type = iter_next_type.get_ptr_to()

    obj_type = fly_obj.get_py_obj_type(visitor.get_builder(), obj)
    iter_next_ptr = _type.py_object_type_get_iter_next(visitor, obj_type)
    iter_next_ptr = builder.ptr_cast(iter_next_ptr, iter_next_type.get_ptr_to())
    iter_next = builder.load(iter_next_ptr)

    is_next_null = builder.eq(iter_next, builder.const_null(iter_next_type))

    next_call_block = builder.create_block()
    normal_call_block = builder.create_block()
    continue_block = builder.create_block()

    builder.cond_br(is_next_null, normal_call_block, next_call_block)

    builder.set_insert_block(next_call_block)
    builder.store(builder.call_ptr(iter_next, [obj]), result)
    builder.br(continue_block)

    builder.set_insert_block(normal_call_block)
    builder.store(
        caller.call_obj(visitor, "__next__", obj, lang_type.get_python_obj_type(), [], [], {}, False, False)[1],
        result)
    builder.br(continue_block)

    builder.set_insert_block(continue_block)
    return builder.load(result)


def call_iter_iter(visitor, obj: int):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    result = visitor.generate_entry_block_var(code_type.get_py_obj_ptr(code_gen))

    iter_next_type = code_type.get_func(code_type.get_py_obj_ptr(code_gen), [code_type.get_py_obj_ptr(code_gen)])
    iter_next_type = iter_next_type.get_ptr_to()

    obj_type = fly_obj.get_py_obj_type(visitor.get_builder(), obj)
    iter_next_ptr = _type.py_object_type_get_iter(visitor, obj_type)
    iter_next_ptr = builder.ptr_cast(iter_next_ptr, iter_next_type.get_ptr_to())
    iter_next = builder.load(iter_next_ptr)

    is_next_null = builder.eq(iter_next, builder.const_null(iter_next_type))

    next_call_block = builder.create_block()
    normal_call_block = builder.create_block()
    continue_block = builder.create_block()

    builder.cond_br(is_next_null, normal_call_block, next_call_block)

    builder.set_insert_block(next_call_block)
    builder.store(builder.call_ptr(iter_next, [obj]), result)
    builder.br(continue_block)

    builder.set_insert_block(normal_call_block)
    builder.store(
        caller.call_obj(visitor, "__iter__", obj, lang_type.get_python_obj_type(), [], [], {}, False, False)[1], result)
    builder.br(continue_block)
    builder.set_insert_block(continue_block)
    return builder.load(result)


def call_iter_next_direct(visitor, obj):
    """
    Directly take the object and call the iter func on it, without any validations
    """
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    iter_next_type = code_type.get_func(code_type.get_py_obj_ptr(code_gen), [code_type.get_py_obj_ptr(code_gen)])
    iter_next_type = iter_next_type.get_ptr_to()

    obj_type = fly_obj.get_py_obj_type(visitor.get_builder(), obj)
    iter_next_ptr = _type.py_object_type_get_iter_next(visitor, obj_type)
    iter_next_ptr = builder.ptr_cast(iter_next_ptr, iter_next_type.get_ptr_to())
    iter_next = builder.load(iter_next_ptr)
    return builder.call_ptr(iter_next, [obj])

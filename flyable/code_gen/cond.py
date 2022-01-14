import flyable.code_gen.list as _list
import flyable.code_gen.dict as _dict
import flyable.data.lang_type as lang_type
import flyable.code_gen.code_type as code_type
import flyable.code_gen.caller as caller
import flyable.data.type_hint as hint
import flyable.code_gen.debug as debug
import flyable.code_gen.ref_counter as ref_counter


def value_to_cond(visitor, value_type, value):
    """
    Convert the value into an integer usable into a conditional branching
    """

    code_gen, builder = visitor.get_code_gen(), visitor.get_builder()
    if value_type.is_int() or value_type.is_bool():
        return value_type, value  # int and bool doesn't need conversion
    elif value_type.is_dec():
        return lang_type.get_bool_type(), builder.int_cast(value, code_type.get_int1())
    elif value_type.is_obj() or value_type.is_python_obj():
        return lang_type.get_bool_type(), test_obj_true(visitor, value_type, value)
    elif value_type.is_list():
        list_len = _list.python_list_len(visitor, value)
        return lang_type.get_bool_type(), builder.gt(list_len, builder.const_int64(0))
    elif value_type.is_dict():
        dict_len = _dict.python_dict_len(visitor, value)
        return lang_type.get_bool_type(), builder.gt(dict_len, builder.const_int(0))


def test_obj_true(visitor, value_type, value):
    """
    This function implements quicker way to test if a condition is True.
    - We first test if it's the true object.
    - If it's not we call the __bool__ function
    - We test if the return of that is true
    """
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    result = visitor.generate_entry_block_var(code_type.get_int1())

    true_ptr = builder.global_var(code_gen.get_true())
    true_value = builder.load(true_ptr)

    is_true = builder.eq(value, true_value)
    true_block = builder.create_block()
    test_true_with_call_block = builder.create_block()
    builder.cond_br(is_true, true_block, test_true_with_call_block)

    builder.set_insert_block(true_block)
    builder.store(builder.const_int1(True), result)
    continue_block = builder.create_block()
    builder.br(continue_block)

    builder.set_insert_block(test_true_with_call_block)

    cond_type, cond_value = caller.call_obj(visitor, "__bool__", value, value_type, [], [])

    false_block = builder.create_block()
    if cond_type.is_python_obj() or cond_type.is_collection() or cond_type.is_obj():
        is_true_2 = builder.eq(cond_value, true_value)
        ref_counter.ref_decr_incr(visitor, cond_type, cond_value)
        builder.cond_br(is_true_2, true_block, false_block)
    elif cond_type.is_bool():
        builder.cond_br(cond_value, true_block, false_block)
    elif cond_type.is_int():
        builder.cond_br(builder.int_cast(cond_value, code_type.get_int1()), true_block, false_block)
    else:
        error_str = "__bool__ should return bool, returned '" + cond_type.to_str(code_gen.get_data()) + "' instead"
        visitor.get_parser().throw_error(error_str, visitor.get_current_node().line_no, 0)

    builder.set_insert_block(false_block)
    builder.store(builder.const_int1(False), result)
    builder.br(continue_block)

    builder.set_insert_block(continue_block)
    return builder.load(result)

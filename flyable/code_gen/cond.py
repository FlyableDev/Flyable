import flyable.code_gen.list as _list
import flyable.code_gen.dict as _dict
import flyable.data.lang_type as lang_type
import flyable.code_gen.code_type as code_type
import flyable.code_gen.caller as caller


def value_to_cond(code_gen, builder, parser, value_type, value):
    """
    Convert the value into an integer usable into a conditional branching
    """
    if value_type.is_int() or value_type.is_bool():
        return value_type, value  # int and bool doesn't need conversion
    elif value_type.is_dec():
        return lang_type.get_bool_type(), builder.int_cast(value, code_type.get_int1())
    elif value_type.is_obj() or value_type.is_python_obj():
        cond_type, cond_value = caller.call_obj(code_gen, builder, parser, "__bool__", value_type, value,
                                                [value], [value_type])
        if cond_type.is_python_obj():
            return lang_type.get_python_obj_type(), builder.eq(cond_value, builder.load(code_gen.get_true()))
        elif cond_type.is_bool() or cond_type.is_int():
            return cond_type, cond_value
        else:
            parser.throw_error("__bool__ should return bool, returned" + cond_type.to_str(code_gen.get_data()), 0, 0)
    elif value_type.is_list():
        list_len = _list.python_list_len(code_gen, builder, value)
        return lang_type.get_int_type(), builder.gt(list_len, builder.const_int64(0))
    elif value_type.is_dict():
        dict_len = _dict.python_dict_len(code_gen, builder, value)
        return lang_type.get_bool_type(), builder.gt(dict_len, builder.const_int(0))

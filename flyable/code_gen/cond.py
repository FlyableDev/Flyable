from __future__ import annotations
from typing import TYPE_CHECKING
import flyable.code_gen.list as _list
import flyable.code_gen.tuple as _tuple
import flyable.code_gen.set as _set
import flyable.code_gen.dict as _dict
import flyable.data.lang_type as lang_type
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as _gen

if TYPE_CHECKING:
    from flyable.parse.parser import ParserVisitor


def value_to_cond(visitor: ParserVisitor, value_type: lang_type.LangType, value: int):
    """
    Convert the value into an integer usable into a conditional branching
    """

    code_gen, builder = visitor.get_code_gen(), visitor.get_builder()
    if value_type.is_int():
        return lang_type.get_bool_type(), builder.int_cast(value, code_type.get_int1())
    elif value_type.is_bool():  # bool doesn't need conversion
        return value_type, value
    elif value_type.is_dec():
        return lang_type.get_bool_type(), builder.int_cast(value, code_type.get_int1())
    elif value_type.is_list():
        list_len = _list.python_list_len(visitor, value)
        return lang_type.get_bool_type(), builder.gt(list_len, builder.const_int64(0))
    elif value_type.is_tuple():
        tuple = builder.ptr_cast(value, code_gen.get_py_tuple_struct().to_code_type().get_ptr_to())
        tuple_len_ptr = _tuple.python_tuple_get_size_ptr(visitor, tuple)
        tuple_len = visitor.get_builder().load(tuple_len_ptr)
        return lang_type.get_bool_type(), builder.gt(tuple_len, builder.const_int64(0))
    elif value_type.is_set():
        set_len = _set.python_set_len(visitor, value)
        return lang_type.get_bool_type(), builder.gt(set_len, builder.const_int64(0))
    elif value_type.is_dict():
        dict_len = _dict.python_dict_len(visitor, value)
        return lang_type.get_bool_type(), builder.gt(dict_len, builder.const_int64(0))
    elif value_type.is_obj() or value_type.is_python_obj():
        return lang_type.get_bool_type(), test_obj_true(visitor, value_type, value)


def test_obj_true(visitor: ParserVisitor, value_type: lang_type.LangType, value: int):
    """
    This function implements quicker way to test if an python object is true

    Here is the C code from CPython that does that :
    int PyObject_IsTrue(PyObject *v)
{
    Py_ssize_t res;
    if (v == Py_True)
        return 1;
    if (v == Py_False)
        return 0;
    if (v == Py_None)
        return 0;
    else if (Py_TYPE(v)->tp_as_number != NULL &&
             Py_TYPE(v)->tp_as_number->nb_bool != NULL)
        res = (*Py_TYPE(v)->tp_as_number->nb_bool)(v);
    else if (Py_TYPE(v)->tp_as_mapping != NULL &&
             Py_TYPE(v)->tp_as_mapping->mp_length != NULL)
        res = (*Py_TYPE(v)->tp_as_mapping->mp_length)(v);
    else if (Py_TYPE(v)->tp_as_sequence != NULL &&
             Py_TYPE(v)->tp_as_sequence->sq_length != NULL)
        res = (*Py_TYPE(v)->tp_as_sequence->sq_length)(v);
    else
        return 1;
    /* if it is negative, it should be either -1 or -2 */
    return (res > 0) ? 1 : Py_SAFE_DOWNCAST(res, Py_ssize_t, int);
}
    """

    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()
    if value_type.is_int():
        return builder.int_cast(value, code_type.get_int1())
    elif value_type.is_dec():
        return builder.eq(value, builder.const_float64(0.0))
    elif value_type.is_list():
        list_size = _list.python_list_len(visitor, value)
        return builder.lt(list_size, builder.const_int64(0))
    else:
        is_true_func = code_gen.get_or_create_func("PyObject_IsTrue", code_type.get_int32(),
                                                   [code_type.get_py_obj_ptr(code_gen)], _gen.Linkage.EXTERNAL)
        is_true_value = builder.call(is_true_func, [value])
        return builder.ne(is_true_value, builder.const_int32(0))

    """
    TODO: IMPLEMENT THE FULL TEST TO AVOID PyObject_IsTrue FUNCTION CALL
    cond_result = visitor.generate_entry_block_var(code_gen, code_type.get_int1())
    builder.store(cond_result, builder.const_int1(False))

    test_true_block = builder.create_block("Is the object True")
    test_false_block = builder.create_block("Is the object False")
    test_none_block = builder.create_block("Is the object None")
    test_number_protocol_block = builder.create_block("Test with the number protocol")
    test_mapping_protocol_block = builder.create_block("Test with the mapping protocol")
    test_sequence_protocol_block = builder.create_block("Test with the sequence protocol")
    value_true_block = builder.create_block("True block")
    else_block = builder.create_block("Else block")
    continue_block = builder.create_block("Continue block")

    builder.br(test_true_block)
    builder.set_insert_block(test_true_block)
    true_value = builder.global_var(code_gen.get_true())
    is_true = builder.eq(true_value, value)
    builder.cond_br(is_true, value_true_block, test_false_block)

    builder.set_insert_block(test_false_block)
    false_value = builder.global_var(code_gen.get_true())
    is_false = builder.eq(false_value, value)
    builder.cond_br(is_false, continue_block, test_none_block)

    builder.set_insert_block(test_none_block)
    none_value = builder.global_var(code_gen.get_none())
    is_none = builder.eq(none_value, test_none_block)
    """

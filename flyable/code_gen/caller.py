"""
Module that handles function calls.
Specifically Python ones
"""
import copy
import flyable.code_gen.code_type as code_type
import flyable.code_gen.exception as excp
import flyable.code_gen.fly_obj as fly_obj
import flyable.code_gen.function as function
import flyable.code_gen.iterator as _iter
import flyable.code_gen.number as num
import flyable.code_gen.ref_counter as ref_counter
import flyable.code_gen.rich_compare as rich_compare
import flyable.code_gen.runtime as runtime
import flyable.data.lang_type as lang_type
import flyable.data.type_hint as hint
import flyable.parse.adapter as adapter
import flyable.parse.shortcut as shortcut
from flyable.parse.parser_visitor import ParserVisitor


def call_obj(visitor: ParserVisitor, func_name: str, obj: int, obj_type: lang_type.LangType, args: list[int],
             args_type: list[lang_type.LangType], kwargs: dict[int, int], optional=False,
             protocol=True, shortcuts=True) -> tuple[lang_type.LangType | None, int | None]:
    """
    Call a method independent from the called type.
    There is 3 calls scenario:
    - Direct flyable method call
    - Virtual flyable method call
    - Python runtime method call
    """
    if obj_type.is_obj():
        # Traditional and direct obj call
        called_class = visitor.get_data().get_class(obj_type.get_id())
        called_func = called_class.get_func(func_name)
        if called_func is None:
            if optional:
                return None, None
            raise Exception(f"Function {func_name} could not be called. Not found in class {called_class.get_name()}")

        called_impl = adapter.adapt_func(
            called_func,
            [obj_type] + args_type,
            visitor.get_data(),
            visitor.get_parser(),
        )
        if called_impl is None:
            raise Exception(f"Could not create the specialized function {func_name}. Invalid function args.")

        return_type = called_impl.get_return_type()
        return_type.add_hint(hint.TypeHintRefIncr())
        code_func = called_impl.get_code_func()
        if code_func is None:
            raise Exception(f"Function {called_impl} has no code_func")
        return return_type, visitor.get_builder().call(
            code_func, [obj] + args
        )
    elif obj_type.is_python_obj() or obj_type.is_collection() or obj_type.is_primitive():
        did_caller_conversion = False
        # The caller can be a primitive, convert if it's the case
        if obj_type.is_primitive():
            did_caller_conversion = True
            obj_type, obj = runtime.value_to_pyobj(
                visitor.get_code_gen(), visitor.get_builder(), obj, obj_type
            )
        # the args for the different handlers
        handlers_args = [visitor, func_name, obj, obj_type, args, args_type, kwargs]
        nb_args = len(args)

        # Maybe there is a shortcut available to skip the python call
        found_shortcut = shortcut.get_obj_call_shortcuts(obj_type, args_type, func_name)
        if found_shortcut is not None:
            result = found_shortcut.parse(
                visitor, obj_type, obj, copy.copy(args_type), copy.copy(args)
            )
        elif not protocol:
            result = _handle_default(*handlers_args)

        # Special case where the call is a binary number protocol
        elif num.is_number_binary_func_valid(func_name, nb_args):  # Number protocol
            return _handle_binary_number_protocol(*handlers_args)

        # Special case where the call is a ternary number protocol
        elif num.is_number_ternary_func_valid(func_name, nb_args) or (
                num.handle_pow_func_special_case(func_name, args, args_type, visitor)
        ):
            return _handle_ternary_number_protocol(*handlers_args)
            # return _handle_default(*handlers_args)

        # Special case where the call is an inquiry number protocol
        elif num.is_number_inquiry_func_valid(func_name, nb_args):
            result = _handle_inquiry_number_protocol(*handlers_args)

        elif _iter.is_iter_func_name(func_name) and len(args) == 0:  # Iter protocol
            return lang_type.get_python_obj_type(
                hint.TypeHintRefIncr()
            ), _iter.call_iter_protocol(visitor, func_name, obj)
        elif rich_compare.is_func_name_rich_compare(func_name) and len(args) == 1:  # Rich Compare protocol
            instance_type = fly_obj.get_py_obj_type(visitor.get_builder(), obj)
            result = rich_compare.call_rich_compare_protocol(
                visitor, func_name, obj_type, obj, instance_type, args_type, args
            )
            return lang_type.get_python_obj_type(hint.TypeHintRefIncr()), result
        else:  # Python call
            result = _handle_default(*handlers_args)

        if did_caller_conversion:
            ref_counter.ref_decr_incr(visitor, obj_type, obj)

        return result

    else:
        raise ValueError(
            "Type un-callable: "
            + obj_type.to_str(visitor.get_data())
            + " for method "
            + func_name
        )


def _handle_binary_number_protocol(visitor: ParserVisitor, func_name: str, obj: int, obj_type: lang_type.LangType, args: list[int], args_type: list[lang_type.LangType]):
    instance_type = fly_obj.get_py_obj_type(visitor.get_builder(), obj)
    return lang_type.get_python_obj_type(hint.TypeHintRefIncr()), num.call_number_protocol(
        visitor, func_name, obj_type, obj, instance_type, args_type, args
    )


def _handle_inquiry_number_protocol(visitor: ParserVisitor, func_name: str, obj: int, obj_type: lang_type.LangType, args: list[int], args_type: list[lang_type.LangType]):
    instance_type = fly_obj.get_py_obj_type(visitor.get_builder(), obj)
    return lang_type.get_bool_type(), num.call_number_protocol(
        visitor, func_name, obj_type, obj, instance_type, args_type, args
    )


def _handle_ternary_number_protocol(visitor: ParserVisitor, func_name: str, obj: int, obj_type: lang_type.LangType, args: list[int], args_type: list[lang_type.LangType]):
    instance_type = fly_obj.get_py_obj_type(visitor.get_builder(), obj)
    return lang_type.get_python_obj_type(hint.TypeHintRefIncr()), num.call_number_protocol(
        visitor, func_name, obj_type, obj, instance_type, args_type, args
    )


def _handle_default(visitor: ParserVisitor, func_name: str, obj: int, obj_type: lang_type.LangType, args: list[int], args_type: list[lang_type.LangType], kwargs: dict[int, int]):
    py_args = copy.copy(args)
    args_type = copy.copy(args_type)

    for i, (arg, arg_type) in enumerate(zip(py_args, args_type)):
        args_type[i], py_args[i] = runtime.value_to_pyobj(
            visitor.get_code_gen(), visitor.get_builder(), arg, arg_type
        )

    return_type = lang_type.get_python_obj_type()
    return_type.add_hint(hint.TypeHintRefIncr())
    result = return_type, generate_python_call(visitor, obj, func_name, py_args, kwargs)
    ref_counter.ref_decr_multiple_incr(visitor, args_type, py_args)
    return result


# https://docs.python.org/3/c-api/method.html
def generate_python_call(visitor: ParserVisitor, obj: int, func_name: str, args: list[int], kwargs: dict[int, int]):
    code_gen, builder = visitor.get_code_gen(), visitor.get_builder()

    # the found attribute is the callable function
    func_to_call = fly_obj.py_obj_get_attr(visitor, obj, func_name)

    call_result_var = visitor.generate_entry_block_var(code_type.get_py_obj_ptr(code_gen))

    callable_type = fly_obj.get_py_obj_type(visitor.get_builder(), func_to_call)

    tp_flag = function.py_obj_type_get_tp_flag_ptr(visitor, callable_type)
    tp_flag = builder.load(tp_flag)

    has_vector_call_tpflag = builder._and(tp_flag, builder.const_int32(2048))  # Does the type flags contain Py_TPFLAGS_HAVE_VECTORCALL

    can_vec_based_on_flag = builder.ne(has_vector_call_tpflag, builder.const_int32(0))
    vector_call_ptr = function.get_vector_call_ptr(visitor, callable_type)
    vector_call_ptr_not_null = builder.ne(builder.ptr_cast(vector_call_ptr, code_type.get_int8_ptr()),
                                          builder.const_null(code_type.get_int8_ptr()))

    can_vec = builder._and(can_vec_based_on_flag, vector_call_ptr_not_null)
    vector_call_block = builder.create_block("Vector call")
    tp_call_block = builder.create_block("Tp call")

    builder.cond_br(can_vec, vector_call_block, tp_call_block)

    builder.set_insert_block(vector_call_block)
    vec_result = function.call_py_func_vec_call(visitor, obj, func_to_call, args, kwargs, vector_call_ptr)
    builder.store(vec_result, call_result_var)
    continue_block = builder.create_block("After Call")
    builder.br(continue_block)

    builder.set_insert_block(tp_call_block)
    tp_result = function.call_py_func_tp_call(visitor, obj, func_to_call, args, kwargs)
    builder.store(tp_result, call_result_var)
    builder.br(continue_block)

    builder.set_insert_block(continue_block)

    result = builder.load(call_result_var)
    ref_counter.ref_decr(visitor, lang_type.get_python_obj_type(), func_to_call)

    excp.py_runtime_print_error(code_gen, builder)
    excp.check_excp(visitor, result)

    return result


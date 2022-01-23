from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flyable.parse.parser import Parser
    from flyable.code_gen.code_gen import CompData, CodeGen
    from flyable.data.lang_type import LangType
    from flyable.data.lang_func import LangFunc

import flyable.data.lang_func_impl as lang_func_impl
import flyable.data.type_hint as hint
from flyable.parse.variable import Variable
from flyable.debug.debug_flags import DebugFlags, debug_flag_enabled


def adapt_call(func_name: str, call_type: LangType, args, comp_data: CompData, parser: Parser, codegen: CodeGen):
    """
    Handle the logic to make the function call possible.
    If it's a Flyable optimized object, it will specialise a function.
    Also handle Python object but doesn't do anything with it at the moment.
    """
    if call_type.is_obj():
        _class = comp_data.get_class(call_type.get_id())
        func = _class.get_func(func_name)
        if func is not None:
            return adapt_func(func, args, comp_data, parser)
    elif call_type.is_python_obj():
        return call_type

    # Any other type doesn't required the class
    return call_type


def adapt_func(func: LangFunc, args, comp_data: CompData, parser: Parser):
    """
    Specialise a function to the given arguments.
    Return an already specialise one if a matching one found.
    """
    if __validate(func, args):
        adapted_impl = func.find_impl_by_signature(args)
        if adapted_impl is not None:
            if not adapted_impl.get_parse_status() == lang_func_impl.LangFuncImpl.ParseStatus.ENDED:
                parser.parse_func(func)
        else:  # Need to create a new implementation
            adapted_impl = lang_func_impl.LangFuncImpl()
            adapted_impl.set_impl_type(lang_func_impl.FuncImplType.SPECIALIZATION)
            for arg in args:
                # new_arg = copy.deepcopy(arg)
                # hint.remove_hint_type(new_arg, hint.TypeHintRefIncr)
                adapted_impl.add_arg(arg)
            func.add_impl(adapted_impl)
            parser.get_code_gen().gen_func(adapted_impl)
            parser.parse_impl(adapted_impl)

        return adapted_impl

    return None


def adapt_all_python_impl(comp_data: CompData, parser: Parser):
    """
    Create an adaption of all functions and methods
    """
    # Start by class impl
    for i in range(comp_data.get_classes_count()):
        _class = comp_data.get_class(i)
        for j in range(_class.get_funcs_count()):
            current_func = _class.get_func(j)
            __adapt_python_impl(current_func, comp_data, parser)

    # And now all functions
    for i in range(comp_data.get_funcs_count()):
        current_func = comp_data.get_func(i)
        __adapt_python_impl(current_func, comp_data, parser)


def __adapt_python_impl(func: LangFunc, comp_data: CompData, parser: Parser):
    tp_adapted_impl = func.get_tp_call_impl()
    vec_adapted_impl = func.get_vec_call_impl()

    if debug_flag_enabled(DebugFlags.PRINT_FUNC_IMPL):
        print(f"{tp_adapted_impl=}")
        print(f"{vec_adapted_impl=}")

    if tp_adapted_impl.get_code_func() is None:
        parser.get_code_gen().gen_func(tp_adapted_impl)
    parser.parse_impl(tp_adapted_impl)

    if vec_adapted_impl.get_code_func() is None:
        parser.get_code_gen().gen_func(vec_adapted_impl)
    parser.parse_impl(vec_adapted_impl)


def __validate(func, args):
    """
    Make sure the function args count is compatible
    """
    min_args = func.get_min_args()
    max_args = func.get_max_args()
    args_size = len(args)
    return min_args <= args_size and (args_size <= max_args or max_args == -1)

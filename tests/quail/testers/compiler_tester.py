from __future__ import annotations

import builtins
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from flyable.data import lang_type
from flyable.data.comp_data import CompData
from flyable.data.lang_type import LangType
from flyable.tool.utils import find_first
import flyable.data.type_hint as hint

if TYPE_CHECKING:
    from flyable.data.lang_func import LangFunc
    from flyable.data.lang_func_impl import LangFuncImpl

from functools import wraps

import flyable.compiler as comp


def _into_lang_type(arg_type: type):
    primitive_types = {
        "int": lang_type.get_int_type(),
        "float": lang_type.get_dec_type(),
        "bool": lang_type.get_bool_type(),
        "set": lang_type.get_set_of_python_obj_type(),
        "dict": lang_type.get_dict_of_python_obj_type(),
        "list": lang_type.get_list_of_python_obj_type(),
        "tuple": lang_type.get_tuple_of_python_obj_type()
    }
    if arg_type.__name__ not in primitive_types:
        return lang_type.get_python_obj_type(hint.TypeHintPythonType(arg_type.__name__))
    return primitive_types[arg_type.__name__]


@dataclass
class FunctionTester:
    __data: CompData
    func: LangFunc

    def has_impl(self, *args_type: type, return_type: type = None):
        name = self.func.get_name()
        lang_args_type = [_into_lang_type(arg_type) for arg_type in args_type]
        if self.func.find_impl_by_signature(lang_args_type) is not None:
            return self
        assert False, f"The function {name!r} doesn't have an implentation that matches {name}{args_type!r}."


@dataclass()
class CompilerResult:
    """"""

    __data: CompData
    functions: list[LangFunc] = field(default_factory=list)

    def assert_func(self, func_name: str):
        func = find_first(lambda f: f.get_name() == func_name, self.functions)
        assert func, f"There is no function defined with name {func_name!r}."
        return FunctionTester(self.__data, func)


class FlyCompilerTester(comp.Compiler):
    def __init__(self):
        super().__init__()
        self.__results = CompilerResult(self._data)
        self.__hijack_parser()

    def __hijack_parser(self):
        def wrapper(f):
            @wraps(f)
            def new_parse_impl(func_impl: LangFuncImpl):
                self.__results.functions.append(func_impl.get_parent_func())
                f(func_impl)

            return new_parse_impl

        self._parser.parse_impl = wrapper(self._parser.parse_impl)

    @property
    def results(self):
        return self.__results

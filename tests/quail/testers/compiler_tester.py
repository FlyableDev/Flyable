from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from flyable.data import lang_type
from flyable.data.comp_data import CompData
from flyable.tool.utils import find_first

from tests.quail.testers.func_tester import FunctionTester

if TYPE_CHECKING:
    from flyable.data.lang_func import LangFunc
    from flyable.data.lang_func_impl import LangFuncImpl

from functools import wraps

import flyable.compiler as comp





@dataclass()
class CompilerResult:
    """"""

    __data: CompData
    functions: set[LangFunc] = field(default_factory=set)

    def assert_func(self, func_name: str):
        """
        Returns a new FunctionTester wrapping the function with a matching name
        This method asserts that the function exists, and will raise an AssertionError if it doesn't

        :param func_name: the name of the function
        :returns: A FunctionTester to analyse furter the function
        :raises AssertionError: if the function doesn't exist
        """
        func = find_first(lambda f: f.get_name() == func_name, self.functions)
        assert func, f"There are no functions defined with name {func_name!r}."
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
                self.__results.functions.add(func_impl.get_parent_func())
                f(func_impl)

            return new_parse_impl

        self._parser.parse_impl = wrapper(self._parser.parse_impl)

    @property
    def results(self):
        return self.__results

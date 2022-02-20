from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from flyable.data import lang_type
from flyable.data.comp_data import CompData
from flyable.parse.context import Context
from flyable.tool.utils import find_first

from tests.quail.testers.func_tester import FunctionTester
from tests.quail.testers.variable_tester import VariableTester

if TYPE_CHECKING:
    from flyable.data.lang_type import LangType
    from flyable.data.lang_func_impl import LangFuncImpl

from flyable.parse.variable import Variable
from flyable.data.lang_func import LangFunc

from functools import wraps

import flyable.compiler as comp


@dataclass()
class CompilerResult:
    """"""

    __data: CompData
    functions: set[LangFunc] = field(default_factory=set)
    variables: set[Variable] = field(default_factory=set)

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

    def assert_var(self, var_name: str):
        var = find_first(lambda v: v.get_name() == var_name, self.variables)
        assert var, f"There are no variables defined with name {var_name!r}."
        return VariableTester(self.__data, var)


class FlyCompilerTester(comp.Compiler):
    def __init__(self):
        super().__init__()
        self.__results = CompilerResult(self._data)
        self.__hijack(LangFunc, self.__results.functions)
        self.__hijack(Variable, self.__results.variables)

    @staticmethod
    def __hijack(cls, lst: set):
        def wrapper(f):
            @wraps(f)
            def new_init(_self, *args, **kwargs):
                f(_self, *args, **kwargs)
                lst.add(_self)

            return new_init

        cls.__init__ = wrapper(cls.__init__)

    @property
    def results(self):
        return self.__results

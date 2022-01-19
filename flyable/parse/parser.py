from __future__ import annotations

import ast
from typing import TYPE_CHECKING, Any

from flyable.debug.debug_flags import DebugFlags, value_if_debug

if TYPE_CHECKING:
    from flyable.code_gen.code_gen import CodeGen

import flyable.data.lang_func_impl as impl
from flyable.data.error_thrower import ErrorThrower
from flyable.debug import parser_analyser
from flyable.parse.parser_visitor import ParserVisitor


class Parser(ErrorThrower):
    def __init__(self, data, code_gen: CodeGen):
        super().__init__()
        self.__data = data
        self.__code_gen = code_gen

    def parse_func(self, func):
        """
        This function parse the "unknown" implementation.
        It's most use to detect parsing errors.
        """
        func_impl = func.get_unknown_impl()
        self.parse_impl(func_impl)

    def parse_impl(self, func_impl):
        if not func_impl.is_unknown():
            if (
                func_impl.get_parse_status()
                == impl.LangFuncImpl.ParseStatus.NOT_STARTED
            ):
                func_impl.set_parse_status(impl.LangFuncImpl.ParseStatus.STARTED)
                for i, e in enumerate(func_impl.args_iter()):
                    new_var = func_impl.get_context().add_var(
                        func_impl.get_parent_func().get_arg(i).arg, e
                    )
                    new_var.set_is_arg(True)

                vis = value_if_debug(
                    ParserVisitor(self, self.__code_gen, func_impl),
                    parser_analyser.ParseAnalyser(self, self.__code_gen, func_impl),
                    DebugFlags.SHOW_OUTPUT_BUILDER,
                )

                vis.parse()

    def get_code_gen(self):
        return self.__code_gen

    def get_data(self):
        return self.__data

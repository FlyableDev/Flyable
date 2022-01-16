import ast
from typing import Any

import flyable.data.lang_func_impl as impl
from flyable.data.error_thrower import ErrorThrower
from flyable.parse import parser_analyser
from flyable.parse.parser_visitor import ParserVisitor


class Parser(ErrorThrower):

    def __init__(self, data, code_gen):
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
            if func_impl.get_parse_status() == impl.LangFuncImpl.ParseStatus.NOT_STARTED:
                func_impl.set_parse_status(impl.LangFuncImpl.ParseStatus.STARTED)
                for i, e in enumerate(func_impl.args_iter()):
                    new_var = func_impl.get_context().add_var(func_impl.get_parent_func().get_arg(i).arg, e)
                    new_var.set_is_arg(True)
                #vis = ParserVisitor(self, self.__code_gen, func_impl)
                vis = parser_analyser.ParseAnalyser(self, self.__code_gen, func_impl)
                vis.setup()
                vis.parse()
                func_impl.set_parse_status(impl.LangFuncImpl.ParseStatus.ENDED)

    def get_code_gen(self):
        return self.__code_gen

    def get_data(self):
        return self.__data

from typing import Any
import ast
from flyable.data.error_thrower import ErrorThrower
from flyable.parse.parser_visitor import ParserVisitor


class Parser(ErrorThrower):

    def __init__(self):
        super().__init__()
        self.__func = None
        self.__comp_data = None

    def parse_func(self, comp_data, func):
        self.__comp_data = comp_data
        self.__func = func
        func_impl = func.get_unknown_impl()
        self.parse_impl(self.__comp_data, func_impl)

    def parse_impl(self, data, func_impl):
        for i, e in enumerate(func_impl.args_iter()):
            new_var = func_impl.get_context().add_var(func_impl.get_parent_func().get_arg(i).arg, e)
            new_var.set_is_arg(True)
        vis = ParserVisitor(self, data)
        vis.parse(func_impl)

    def parse_file(self, file):
        pass

    def parse_class(self, _class):
        pass

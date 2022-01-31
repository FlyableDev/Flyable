import ast
from operator import attrgetter
from typing import Callable

from flyable.debug.debug_flags_list import *
from flyable.parse.parser_visitor import ParserVisitor
from flyable.debug.utils import dprint, dindent_plus, dget_indent, dindent_minus


class ParseAnalyser(ParserVisitor):
    def __init__(self, parser, code_gen, func_impl):
        super().__init__(parser, code_gen, func_impl)
        self.max_depth = FLAG_SHOW_VISIT_AST.value
        self.__setup()

    def __setup(self):
        for method_name in self.__dir__():
            if not method_name.startswith("visit_") or method_name == "visit_node":
                continue
            method = getattr(self, method_name)
            setattr(self, method_name, self.__gen_method(method))

    def __gen_method(self, func: Callable) -> Callable:
        def new_method(node: ast.AST):
            values = self.__get_values(node, 0)
            dprint(f"<{func.__name__} {values}>")
            dindent_plus()
            result = func(node)
            dindent_minus()
            dprint(f"</{func.__name__}>")
            if dget_indent() == 0:
                print()
            return result

        return new_method

    def __get_values(self, node: ast.AST, depth):
        values = {}
        if len(node._fields) == 0:
            return node.__class__.__name__

        if not self.__depth_is_valid(depth):
            return f"<{node.__class__.__name__} .../>"

        for field in node._fields:
            attr = getattr(node, field)
            if isinstance(attr, ast.AST):
                attr = self.__get_values(attr, depth + 1)
            elif isinstance(attr, list):
                attr = [self.__get_values(_attr, depth + 1) for _attr in attr]
            values[field] = attr
        return values

    def __depth_is_valid(self, depth):
        return self.max_depth < 0 or depth < self.max_depth

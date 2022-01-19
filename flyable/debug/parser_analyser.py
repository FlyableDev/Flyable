import ast
from operator import attrgetter
from typing import Callable

from flyable.parse.parser_visitor import ParserVisitor


class ParseAnalyser(ParserVisitor):
    def __init__(self, parser, code_gen, func_impl):
        super().__init__(parser, code_gen, func_impl)
        self.tabs = 0
        self.max_depth = -1
        self.depth = 0
        self.__setup()

    def __setup(self, max_depth: int = -1):
        self.max_depth = max_depth
        for method_name in self.__dir__():
            if not method_name.startswith("visit_"):
                continue
            method = getattr(self, method_name)
            setattr(self, method_name, self.__gen_method(method))

    def __gen_method(self, func: Callable) -> Callable:
        def new_method(node: ast.AST):
            values = self.__get_values(node)
            print("\t" * self.tabs + f"<{func.__name__} {values}>")
            self.tabs += 1
            result = func(node)
            self.tabs -= 1
            print("\t" * self.tabs + f"</{func.__name__}>")
            if self.tabs == 0:
                print()
            return result

        return new_method

    def __get_values(self, node: ast.AST):
        if len(node._fields) == 0:
            return node.__class__.__name__
        values = {}
        for field in node._fields:
            attr = getattr(node, field)
            if isinstance(attr, ast.AST) and self.__depth_is_valid():
                self.depth += 1
                attr = self.__get_values(attr)
                self.depth -= 1
            elif isinstance(attr, list) and self.__depth_is_valid():
                self.depth += 1
                attr = [self.__get_values(_attr) for _attr in attr]
                self.depth -= 1
            values[field] = attr
        return values

    def __depth_is_valid(self):
        return self.max_depth < 0 or self.depth < self.max_depth

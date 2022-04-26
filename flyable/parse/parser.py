from __future__ import annotations

import ast
from _ast import FunctionDef
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from flyable.code_gen.code_gen import CodeGen
    from flyable.data.lang_func_impl import LangFuncImpl
    from flyable.data.comp_data import CompData
    from flyable.parse.parser_visitor import ParserVisitor

import flyable.data.lang_func_impl as impl
from flyable.data.error_thrower import ErrorThrower
import flyable.data.lang_func as lang_func


class Parser(ErrorThrower):
    def __init__(self, data: CompData, code_gen: CodeGen):
        super().__init__()
        self.__data = data
        self.__code_gen = code_gen

    def parse_file(self, file):
        class FuncSearcher(ast.NodeVisitor):
            """
            Internal class used to look at the ast get get functions
            """
            def __init__(self, parser):
                self.__parser = parser
                
            def visit_FunctionDef(self, node: FunctionDef) -> Any:
                node.qualname = f"{file.get_path().replace('/', '.')[1:]}.{node.name}"
                new_func = lang_func.LangFunc(node)
                new_func.set_file(file)
                file.add_func(new_func)
                self.__parser.parse_impl(new_func.get_tp_call_impl())
                self.__parser.parse_impl(new_func.get_vec_call_impl())

        nodes = ast.parse(file.get_text())
        visitor = FuncSearcher(self)
        visitor.visit(nodes)

    def parse_impl(self, func_impl: LangFuncImpl):
        if func_impl.get_parse_status() == impl.LangFuncImpl.ParseStatus.NOT_STARTED:
            func_impl.set_parse_status(impl.LangFuncImpl.ParseStatus.STARTED)
            import flyable.parse.parser_visitor as parser_vis
            vis = parser_vis.ParserVisitor(self, self.__code_gen, func_impl)
            vis.run()

    def get_code_gen(self):
        return self.__code_gen

    def get_data(self):
        return self.__data

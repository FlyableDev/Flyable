import ast
from operator import attrgetter
from typing import Callable

from flyable.code_gen.code_writer import CodeWriter


class CodeWriteAnalyser(CodeWriter):
    def __init__(self):
        super().__init__()

    def setup(self):
        for method_name in self.__dir__():
            if not method_name.startswith("add_"):
                continue
            method = getattr(self, method_name)
            setattr(self, method_name, self.__gen_method(method))

    def __gen_method(self, func: Callable) -> Callable:
        def new_method(value):
            print(f"writing {value} as {func.__name__.split('add_')[0]}")
            result = func(value)
            return result

        return new_method


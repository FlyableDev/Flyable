from __future__ import annotations
import ast
from typing import TYPE_CHECKING, Any, Callable
from flyable.code_gen.code_builder import CodeBuilder
from flyable.code_gen.code_writer import CodeWriter
from flyable.debug.utils import dprint, ddivider

if TYPE_CHECKING:
    from flyable.code_gen.code_gen import CodeFunc

CODE_BUILDER_IDS = [
    "add",
    "sub",
    "mul",
    "div",
    "eq",
    "ne",
    "lt",
    "lte",
    "gt",
    "gte",
    "neg",
    "_and",
    "_or",
    "mod",
    "floor",
    "_not",
    "store",
    "load",
    "br",
    "cond_br",
    "gep",
    "gep2",
    "call",
    "call_ptr",
    "const_int64",
    "const_int32",
    "const_int16",
    "const_int8",
    "const_int1",
    "const_float32",
    "const_float64",
    "const_null",
    "ptr_cast",
    "int_cast",
    "float_cast",
    "int_to_ptr",
    "bit_cast",
    "zext",
    "alloca",
    "ret",
    "ret_void",
    "ret_null",
    "global_var",
    "global_str",
    "func_ptr",
    "size_of_type",
    "size_of_type_ptr_element",
    "print_value_type",
    "debug_op",
    "debug_op2",
]


class CodeBuilderAnalyser(CodeBuilder):
    def __init__(self, func):
        super().__init__(func)
        self.__setup()
        self.__current_method: str = ""
        self.__is_writing_method_id = False

    @property
    def __writer(self) -> CodeWriter:
        return getattr(self, "_CodeBuilder__writer")

    def set_insert_block(self, block: CodeFunc.CodeBlock):
        result = super().set_insert_block(block)
        self.__writer.add_int32 = self.__debug_writer(self.__writer.add_int32)
        return result

    def __setup(self, max_depth: int = -1):
        self.max_depth = max_depth
        for method_name in CODE_BUILDER_IDS:
            method = getattr(self, method_name)
            setattr(self, method_name, self.__gen_method(method))
        # setattr(self, method_name, self.__gen_method(getattr(self, method_name)))

    def __gen_method(self, func: Callable) -> Callable:
        def new_method(*args, **kwargs):
            self.__current_method = func.__name__
            self.__is_writing_method_id = True
            result = func(*args, **kwargs)
            dprint(f"args: {args}")
            dprint(f"{result=}")
            ddivider()
            return result

        return new_method

    def __debug_writer(self, func_add_int_32):
        def debug_add_int32(value):
            if self.__is_writing_method_id:
                dprint(f"writing {value} ({self.__current_method})")
                self.__is_writing_method_id = False
            result = func_add_int_32(value)
            return result

        return debug_add_int32

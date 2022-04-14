from __future__ import annotations
from typing import TYPE_CHECKING, overload
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen
import flyable.code_gen.ref_counter as ref_count
from flyable.tool.utils import find_first

if TYPE_CHECKING:
    from flyable.parse.parser import ParserVisitor
    from flyable.code_gen.code_type import CodeType
    from flyable.code_gen.code_gen import Linkage, CodeGen
    from flyable.code_gen.code_builder import CodeBuilder

from dataclasses import dataclass


@dataclass
class Fly_CFunction:
    name: str
    return_type: CodeType
    args_type: list[CodeType]
    link: Linkage = gen.Linkage.EXTERNAL

    def get_function(self, code_gen: CodeGen):
        return code_gen.get_or_create_func(**self.__dict__)

    def __call__(
        self, values: list[int], caller: ParserVisitor | tuple[CodeGen, CodeBuilder]
    ):
        if isinstance(caller, ParserVisitor):
            code_gen = caller.get_code_gen()
            builder = caller.get_builder()
        else:
            code_gen, builder = caller
        return builder.call(self.get_function(code_gen), values)


FLY_CFUNCTIONS = [
    Fly_CFunction("flyable_add_impl", code_type.get_void(), [code_type.get_int8_ptr()] * 3),
    Fly_CFunction("flyable_debug_print_ptr", code_type.get_void(), [code_type.get_int8_ptr()]),
    Fly_CFunction("flyable_debug_print_int64", code_type.get_void(), [code_type.get_int64()]),
]


def get_fly_cfunction(name: str):
    return find_first(lambda c_function: c_function.name == name, FLY_CFUNCTIONS)

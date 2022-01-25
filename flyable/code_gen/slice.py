from __future__ import annotations
from typing import TYPE_CHECKING
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen

if TYPE_CHECKING:
    from flyable.parse.parser import ParserVisitor


def py_slice_new(visitor: ParserVisitor, start: int, stop: int, step: int):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    func = code_gen.get_or_create_func("PySlice_New", code_type.get_py_obj_ptr(code_gen),
                                       [code_type.get_py_obj_ptr(code_gen)] * 3, gen.Linkage.EXTERNAL)

    return builder.call(func, [start, stop, step])

from __future__ import annotations
from typing import TYPE_CHECKING
from flyable.code_gen.code_builder import CodeBuilder
import flyable.code_gen.code_type as code_type
from flyable.data.lang_type import LangType

if TYPE_CHECKING:
    from flyable.code_gen.code_gen import Linkage, CodeGen
    from flyable.parse.parser import ParserVisitor


def py_object_is_type(code_gen: CodeGen, builder: CodeBuilder, type: LangType, value, value_to_be):
    func = code_gen.get_or_create_func("PyObject_IsSubclass", code_type.get_int32(), [code_type.get_int8_ptr()], Linkage.EXTERNAL)
    return builder.call(func, [value, value_to_be])


def py_object_type_get_dealloc_ptr(visitor: ParserVisitor, type: int):
    builder = visitor.get_builder()
    return visitor.get_builder().gep(type, builder.const_int32(0), builder.const_int32(6))


def py_object_type_get_tp_as_number_ptr(visitor: ParserVisitor, type: int):
    builder = visitor.get_builder()
    return builder.gep(type, builder.const_int32(0), builder.const_int32(12))


def py_object_type_get_tp_richcompare_ptr(visitor: ParserVisitor, type: int):
    builder = visitor.get_builder()
    return builder.gep(type, builder.const_int32(0), builder.const_int32(24))


def py_object_type_get_iter_next(visitor: ParserVisitor, type: int):
    builder = visitor.get_builder()
    return visitor.get_builder().gep(type, builder.const_int32(0), builder.const_int32(28))


def py_object_type_get_iter(visitor: ParserVisitor, type: int):
    builder = visitor.get_builder()
    return visitor.get_builder().gep(type, builder.const_int32(0), builder.const_int32(27))


def py_object_type_get_vectorcall_offset_ptr(visitor: ParserVisitor, type: int):
    builder = visitor.get_builder()
    return visitor.get_builder().gep(type, builder.const_int32(0), builder.const_int32(7))

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flyable.parse.parser_visitor import ParserVisitor

from ast import Try

import flyable.code_gen.exception as excp
import flyable.code_gen.fly_obj as fly_obj
import flyable.code_gen.code_type as code_type


def parse_try(visitor: ParserVisitor, node: Try):
    builder = visitor.get_builder()
    continue_block = builder.create_block()
    excp_block = builder.create_block()
    excp_not_found_block = builder.create_block()
    else_block = builder.create_block() if node.orelse is not None else None

    visitor.add_except_block(excp_block)
    handlers_block = []
    handlers_cond_block = []
    for _ in node.handlers:
        handlers_block.append(builder.create_block())
        handlers_cond_block.append(builder.create_block())

    visitor.visit_node(node.body)

    builder.br(handlers_cond_block[0])

    if else_block is None:
        builder.br(continue_block)
    else:
        builder.br(else_block)

    builder.set_insert_block(excp_block)

    builder.br(handlers_cond_block[0])

    parse_handlers(visitor, node, handlers_cond_block, handlers_block, continue_block, excp_not_found_block)

    # self.__visit_node(node.finalbody)

    if else_block is not None:
        builder.set_insert_block(else_block)
        visitor.visit_node(node.orelse)
        builder.br(continue_block)

    builder.set_insert_block(continue_block)


def parse_handlers(visitor, try_node, handlers_cond_block, handlers_block, continue_block, excp_not_found_block):
    builder = visitor.get_builder()
    for i, handler in enumerate(try_node.handlers):  # For each exception statement
        visitor.reset_last()
        builder.set_insert_block(handlers_cond_block[i])
        excp_value = excp.py_runtime_get_excp(visitor.get_code_gen(), builder)
        excp_type = fly_obj.get_py_obj_type(builder, excp_value)
        excp_type = builder.ptr_cast(excp_value, code_type.get_py_obj_ptr(visitor.get_code_gen()))
        obj_type, obj_type_value = visitor.visit_node(handler.type)
        type_match = builder.eq(obj_type_value, excp_type)
        other_block = handlers_cond_block[i + 1] if i < len(try_node.handlers) - 1 else excp_not_found_block
        builder.cond_br(type_match, handlers_block[i], other_block)
        builder.br(continue_block)
        builder.set_insert_block(handlers_block[i])
        visitor.visit_node(handler.body)
        builder.br(continue_block)

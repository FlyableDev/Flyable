from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flyable.parse.parser_visitor import ParserVisitor
    from flyable.code_gen.code_gen import CodeBlock
    from ast import expr

from ast import Try

import flyable.code_gen.exception as excp
import flyable.code_gen.fly_obj as fly_obj
import flyable.code_gen.code_type as code_type
import flyable.code_gen.debug as debug
import flyable.code_gen.exception as exception
import flyable.code_gen.runtime as runtime


def parse_try(visitor: ParserVisitor, node: Try):
    """

    :param visitor: current parser_visitor
    :param node: to try node to parse
    """
    """
    How the parsing works
    (goto x => execute x and ignore the rest of the block)
    (|-> x => branch to x)
    >>> start at block
    
    block:
    |> visit node.body (if exception raised -> goto excp_block)
    |> if has_else
        |-> else_block
    |> elif has_finally
        |-> finally_block
    |> else
        |-> continue_block

    excp_block:
    |> if has_handlers
        |-> handlers_cond_block
    |> else
        |-> excp_not_found_block
        
    handler_cond_block:
    |> if error matches 
        |-> handler_block
    |> elif block is the last hadler_cond_block 
        |-> excp_not_found_block
    |> else
        |-> handler_cond_block
    
    excp_not_found_block:
    |> if has_finally
        |-> finally_block
    |> else
        |-> continue_block
    
    else_block:
    |> visit node.orelse
    |> has_finally?
        |-> finally_block
    |> else
        |-> continue_block
    
    finally_block:
    |> visit node.finalbody
        |-> continue_block
    """
    builder = visitor.get_builder()

    has_handlers = len(node.handlers) > 0
    has_else = len(node.orelse) > 0
    has_finally = len(node.finalbody) > 0

    continue_block = builder.create_block("After Try")
    excp_block = builder.create_block("Exceptions Handlers")
    excp_not_found_block = builder.create_block("Exception not found")
    finally_block = builder.create_block("Finally") if has_finally else None
    else_block = builder.create_block("Else") if has_else else None

    # set this except block as the except block to visit when an exception is raised
    visitor.add_except_block(excp_block)

    handlers_block = []
    handlers_cond_block = []
    for handler in node.handlers:
        handlers_block.append(builder.create_block(f"Except body: {handler.type.id}"))  # type: ignore
        handlers_cond_block.append(builder.create_block(f"Except check: {handler.type.id}"))  # type: ignore

    # visiting the body of the try statement
    visitor.visit_node(node.body)
    if has_else:
        builder.br(else_block)
    elif has_finally:
        builder.br(finally_block)
    else:
        builder.br(continue_block)

    if has_handlers:
        parse_handlers(
            visitor,
            node,
            handlers_cond_block,
            handlers_block,
            continue_block,
            excp_not_found_block,
            finally_block,
        )

        # defining the content of the excp block w/ handlers
        builder.set_insert_block(excp_block)
        builder.br(handlers_cond_block[0])
    else:
        # defining the content of the excp block w/ no handlers
        builder.set_insert_block(excp_block)
        builder.br(excp_not_found_block)
        builder.br(finally_block if has_finally else continue_block)

    # defining the content of the excption not found block
    builder.set_insert_block(excp_not_found_block)
    runtime.py_runtime_object_print(
        visitor.get_code_gen(),
        builder,
        exception.py_runtime_get_excp(visitor.get_code_gen(), builder),
    )
    has_finally and builder.br(finally_block)

    if else_block is not None:
        # defining the content of the else block
        builder.set_insert_block(else_block)
        visitor.visit_node(node.orelse)
        builder.br(finally_block if has_finally else continue_block)

    if finally_block is not None:
        # defining the content of the finally block
        builder.set_insert_block(finally_block)
        visitor.visit_node(node.finalbody)
        builder.br(continue_block)

    # defining the content of the continue block
    builder.set_insert_block(continue_block)


def parse_handlers(
        visitor: ParserVisitor,
        try_node: Try,
        handlers_cond_block: list[CodeBlock],
        handlers_block: list[CodeBlock],
        continue_block: CodeBlock,
        excp_not_found_block: CodeBlock,
        finally_block: CodeBlock,
):
    builder = visitor.get_builder()
    # For each exception statement
    for i, (handler, handler_block, handler_cond_block) in enumerate(
            zip(try_node.handlers, handlers_block, handlers_cond_block)
    ):
        if handler.type is None:
            continue

        visitor.reset_last()
        builder.set_insert_block(handler_cond_block)
        excp_value = excp.py_runtime_get_excp(visitor.get_code_gen(), builder)
        runtime.py_runtime_object_print(
            visitor.get_code_gen(),
            builder,
            excp_value,
        )

        excp_type = fly_obj.get_py_obj_type(builder, excp_value)
        excp_type = builder.ptr_cast(
            excp_value, code_type.get_py_obj_ptr(visitor.get_code_gen())
        )

        obj_type, obj_type_value = visitor.visit_node(handler.type)

        type_match = builder.eq(obj_type_value, excp_type)

        other_block = (
            handlers_cond_block[i + 1]
            if i + 1 < len(try_node.handlers)
            else excp_not_found_block
        )
        end_block = finally_block if finally_block is not None else continue_block
        builder.cond_br(type_match, handler_block, other_block)
        builder.br(end_block)
        builder.set_insert_block(handler_block)
        visitor.visit_node(handler.body)
        builder.br(end_block)

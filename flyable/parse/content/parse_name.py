from __future__ import annotations

import ast
import copy
from typing import TYPE_CHECKING, Callable

import flyable.data.type_hint as hint
from flyable.code_gen import fly_obj, ref_counter, runtime
from flyable.data import lang_type

if TYPE_CHECKING:
    from flyable.parse.parser_visitor import ParserVisitor
    from flyable.code_gen.code_builder import CodeBuilder
    from flyable.data.lang_type import LangType
    from flyable.parse.variable import Variable


def handle_found_var(
        visitor: ParserVisitor,
        found_var: Variable,
        node: ast.Name,
        assign_type: LangType,
        assign_value,
):
    value: int
    _type: LangType
    builder = visitor.get_builder()
    code_gen = visitor.get_code_gen()
    data = visitor.get_data()
    func = visitor.get_func()
    var_name = node.id

    # Imported module, retrieve stored global reference
    if found_var.get_code_gen_value().belongs_to_module():
        variable_reference = builder.global_var(found_var.get_code_gen_value())
        _type = copy.copy(found_var.get_type())
        value = builder.load(variable_reference)

        if _type.is_python_obj():
            _type = lang_type.get_python_obj_type()
            _type.add_hint(hint.TypeHintRefIncr())
            value = fly_obj.py_obj_get_attr(visitor, value, found_var.get_name())
        return _type, value

    _type = found_var.get_type()
    if found_var.is_global():
        value = builder.global_var(found_var.get_code_gen_value())
    elif found_var.get_code_gen_value() is None and not found_var.is_global():
        found_var.set_code_gen_value(
            visitor.generate_entry_block_var(
                found_var.get_type().to_code_type(code_gen), True
            )
        )

    value = found_var.get_code_gen_value()

    if found_var.is_arg():
        value = found_var.get_code_gen_value()
        _type = found_var.get_type()
        return _type, value

    # Args don't live inside an alloca so they don't need to be loaded

    if not isinstance(node.ctx, ast.Store):
        # if found_var.is_global() and found_var.get_context() != func.get_context():
        #    parser.throw_error("Not found variable '" + node.id + "'", node.lineno, node.col_offset)
        value = builder.load(value)
        _type = copy.copy(found_var.get_type())
        _type.add_hint(hint.TypeHintSourceLocalVariable(found_var))

        return _type, value

    # If it tries to assign a global variable in a local context without the global keyword,
    # instead declare a new local variable in the function context
    if found_var.is_global() and found_var.get_context() != func.get_context():
        found_var = func.get_context().add_var(var_name, assign_type)
        alloca_value = visitor.generate_entry_block_var(
            assign_type.to_code_type(code_gen), True
        )
        found_var.set_code_gen_value(alloca_value)
        builder.store(assign_value, alloca_value)
        value = found_var.get_code_gen_value()
        _type = copy.copy(found_var.get_type())
        _type.add_hint(hint.TypeHintSourceLocalVariable(found_var))
        return _type, value

    # Else assign new value to variable
    # Decrement the old content
    old_content = builder.load(value)
    ref_counter.ref_decr_nullable(visitor, found_var.get_type(), old_content)

    # The variable might have a new type
    var_type = lang_type.get_most_common_type(data, found_var.get_type(), assign_type)
    if found_var.get_type() != var_type:
        found_var.set_type(var_type)
        if found_var.is_global():
            data.set_changed(True)
        else:
            reset_visit = True

    # Store the new content
    value_assign = assign_value
    if _type.is_python_obj():
        _, value_assign = runtime.value_to_pyobj(
            code_gen, builder, value_assign, assign_type
        )
    hint.remove_hint_type(_type, hint.TypeHintConstInt)
    builder.store(value_assign, value)
    # last_become_assign()

    return _type, value

from __future__ import annotations

from ast import And, Compare
from typing import TYPE_CHECKING

from flyable.code_gen import op_call, debug, caller, code_type
from flyable.code_gen.tuple import python_tuple_new_alloca, python_tuple_set
from flyable.data import lang_type
from flyable.parse import build_in

if TYPE_CHECKING:
    from flyable.parse.parser_visitor import ParserVisitor

import flyable.code_gen.ref_counter as ref_counter


def parse_compare(visitor: ParserVisitor, node: Compare):
    compare_types = []
    compare_values = []
    first_type, first_value = visitor.visit_node(node.left)
    for op, comparator in zip(node.ops, node.comparators):
        second_type, second_value = visitor.visit_node(comparator)
        result_type, result_value = op_call.cond_op(
            visitor, op, first_type, first_value, second_type, second_value
        )
        compare_types.append(result_type)
        compare_values.append(result_value)
        ref_counter.ref_decr_incr(visitor, first_type, first_value)
        first_type, first_value = second_type, second_value

    ref_counter.ref_decr_incr(visitor, first_type, first_value)

    # debug.flyable_debug_print_int64(visitor.get_code_gen(), visitor.get_builder(),
    #                                 visitor.get_builder().int_cast(compare_values[0], code_type.get_int64()))

    first_value = compare_values[0]
    first_type = compare_types[0]

    if len(node.ops) == 1:
        return first_type, first_value

    builder = visitor.get_builder()

    for comparison_val, comparison_type in zip(compare_values[1:], compare_types[1:]):
        result_type, result_value = lang_type.get_bool_type(), builder._and(first_value, comparison_val)
        ref_counter.ref_decr_multiple_incr(
            visitor, [first_type, comparison_type], [first_value, comparison_val]
        )
        first_type, first_value = result_type, result_value

    return first_type, first_value

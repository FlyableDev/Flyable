from __future__ import annotations

from ast import And, Compare, BitAnd
from functools import reduce
from itertools import pairwise, accumulate
from typing import TYPE_CHECKING
import flyable.data.type_hint as hint

from flyable.code_gen import op_call, debug, caller, code_type
from flyable.code_gen.tuple import python_tuple_new_alloca, python_tuple_set
from flyable.data import lang_type
from flyable.parse import build_in

if TYPE_CHECKING:
    from flyable.data.lang_type import LangType
    from flyable.parse.parser_visitor import ParserVisitor
    from _ast import expr

import flyable.code_gen.ref_counter as ref_counter


def parse_compare(visitor: ParserVisitor, node: Compare):
    builder = visitor.get_builder()

    def compare(
        current: tuple[LangType, int], comparison: tuple[LangType, int]
    ) -> tuple[LangType, int]:
        left_type, left_val = current
        right_type, right_val = comparison

        result = op_call.cond_op(
            visitor, BitAnd(), left_type, left_val, right_type, right_val
        )
        ref_counter.ref_decr_incr(visitor, right_type, right_val)
        print(current)
        print(comparison)
        return result

    def do_cond_op(prev: tuple[LangType, int] | None, current_args):
        left, op, right = current_args
        left_type, left_val = left
        right_type, right_val = right

        result_type, result_val = op_call.cond_op(
            visitor, op, left_type, left_val, right_type, right_val
        )
        # result_type.add_hint(hint.TypeHintRefIncr())
        ref_counter.ref_decr_incr(visitor, left_type, left_val)
        return (
            compare(prev, (result_type, result_val))
            if prev is not None
            else (result_type, result_val)
        )

    comparators = [
        visitor.visit_node(comparator) for comparator in (node.left, *node.comparators)
    ]

    pairs = [
        (comparator[0], node.ops[idx], comparator[1])
        for idx, comparator in enumerate(pairwise(comparators))
    ]

    compare_result = reduce(do_cond_op, pairs, None)
    last_comparator_type, last_comparator_val = comparators[-1]
    ref_counter.ref_decr_incr(visitor, last_comparator_type, last_comparator_val)

    return compare_result

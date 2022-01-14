import ast
import flyable.code_gen.caller as caller
from flyable.data.lang_type import *
import flyable.data.type_hint as hint
import flyable.code_gen.list as gen_list
import  flyable.code_gen.exception as excp
import flyable.code_gen.ref_counter as ref_counter
import flyable.code_gen.debug as debug

def unpack_assignation(visitor, targets, value_type, value, node):
    unpack_block = visitor.get_builder().create_block()
    error_block = visitor.get_builder().create_block()
    continue_block = visitor.get_builder().create_block()

    # TODO: The following works for Tuples and Lists, but we need to support unpacking Iterables
    len_targets = visitor.get_builder().const_int64(len(targets))
    len_value = gen_list.python_list_len(visitor, value)

    test = visitor.get_builder().eq(len_value, len_targets)
    visitor.get_builder().cond_br(test, unpack_block, error_block)
    visitor.get_builder().set_insert_block(unpack_block)

    for i, target in enumerate(targets):
        index_type = get_int_type()
        index_type.add_hint(hint.TypeHintConstInt(i))
        index_value = visitor.get_builder().const_int64(i)
        args_types = [index_type]
        args = [index_value]
        value_type_i, value_i = caller.call_obj(visitor, "__getitem__", value, value_type, args, args_types)
        if not hint.is_incremented_type(value_type_i):
            ref_counter.ref_incr(visitor.get_builder(), value_type_i, value_i)
        if isinstance(target, ast.Tuple) or isinstance(target, ast.List):
            new_targets = []
            for t in target.elts:
                new_targets.append(t)
            unpack_assignation(visitor, new_targets, value_type_i, value_i, node)
        elif isinstance(target, ast.Name):
            visitor.set_assign_type(value_type_i)
            visitor.set_assign_value(value_i)
            visitor.visit_node(target)
        else:
            visitor.get_parser().throw_error("Incorrect target type encountered when unpacking ", node.lineno,
                                         node.end_col_offset)
        ref_counter.ref_decr(visitor, value_type_i, value_i)

    visitor.get_builder().br(continue_block)

    visitor.get_builder().set_insert_block(error_block)
    excp.raise_index_error(visitor)     # value doesn't have as many elements as targets

    visitor.get_builder().set_insert_block(continue_block)
    ref_counter.ref_decr(visitor, value_type, value)

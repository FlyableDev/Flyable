import ast
import flyable.code_gen.caller as caller
from flyable.data.lang_type import *
import flyable.data.type_hint as hint
import flyable.code_gen.list as gen_list
import  flyable.code_gen.exception as excp

def unpack_assignation(visitor, targets, value_type, value, node):
    unpack_block = visitor.get_builder().create_block()
    error_block = visitor.get_builder().create_block()
    continue_block = visitor.get_builder().create_block()

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

    visitor.get_builder().br(continue_block)

    visitor.get_builder().set_insert_block(error_block)
    excp.raise_index_error(visitor)

    visitor.get_builder().set_insert_block(continue_block)


def unpack_for_loop(node, visitor):
    pass

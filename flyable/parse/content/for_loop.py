import ast
import flyable.code_gen.ref_counter as ref_counter
import flyable.code_gen.caller as caller
import flyable.data.type_hint as hint
import flyable.code_gen.exception as excp
import flyable.code_gen.code_type as code_type


def parse_for_loop(node, visitor):
    object_to_iter_on = node.iter
    __for_loop_with_iterators(node, visitor)
    # Check for a very fast for loop in a range


def __for_loop_with_iterators(node, visitor):
    code_gen = visitor.get_code_gen()
    builder = visitor.get_builder()

    name = node.target.id
    iter_type, iter_value = visitor.visit_node(node.iter)

    if not hint.is_incremented_type(iter_type):
        ref_counter.ref_incr(builder, iter_type, iter_value)

    new_var = visitor.get_func().get_context().add_var(name, iter_type)
    alloca_value = visitor.generate_entry_block_var(iter_type.to_code_type(code_gen))
    new_var.set_code_gen_value(alloca_value)
    iterable_type, iterator = caller.call_obj(visitor, "__iter__", iter_value, iter_type, [], [])

    block_for = builder.create_block()

    builder.br(block_for)
    builder.set_insert_block(block_for)

    next_type, next_value = caller.call_obj(visitor, "__next__", iterator, iterable_type, [], [])

    if not hint.is_incremented_type(next_type):
        ref_counter.ref_incr(builder, next_type, next_value)

    builder.store(next_value, new_var.get_code_gen_value())

    null_ptr = builder.const_null(code_type.get_py_obj_ptr(code_gen))

    test = builder.eq(next_value, null_ptr)

    block_continue = builder.create_block()
    block_for_in = builder.create_block()
    block_else = builder.create_block() if node.orelse is not None else None
    if node.orelse is None:
        builder.cond_br(test, block_continue, block_for_in)
    else:
        builder.cond_br(test, block_else, block_for_in)

    # Setup the for loop content
    builder.set_insert_block(block_for_in)
    visitor.add_out_block(block_continue)  # In case of a break we want to jump after the for loop
    visitor.visit(node.body)
    ref_counter.ref_decr(visitor, next_type, next_value)
    visitor.pop_out_block()

    builder.br(block_for)

    if node.orelse is not None:
        builder.set_insert_block(block_else)
        excp.py_runtime_clear_error(code_gen, builder)
        visitor.visit(node.orelse)
        builder.br(block_continue)

    builder.set_insert_block(block_continue)
    ref_counter.ref_decr(visitor, iter_type, iter_value)
    excp.py_runtime_clear_error(code_gen, builder)

from __future__ import annotations

import ast
import copy
from ast import *
from typing import TYPE_CHECKING, Any, Union, TypeAlias, Generic, Type, Optional, TypeVar

import flyable.code_gen.caller as caller
import flyable.code_gen.code_gen as gen
import flyable.code_gen.cond as cond
import flyable.code_gen.debug as debug
import flyable.parse.exception.unsupported as unsupported
import flyable.code_gen.dict as gen_dict
import flyable.code_gen.exception as excp
import flyable.code_gen.fly_obj as fly_obj
import flyable.code_gen.list as gen_list
import flyable.code_gen.module as gen_module
import flyable.code_gen.op_call as op_call
import flyable.code_gen.ref_counter as ref_counter
import flyable.code_gen.runtime as runtime
import flyable.code_gen.set as gen_set
import flyable.code_gen.slice as gen_slice
import flyable.code_gen.tuple as gen_tuple
import flyable.code_gen.unpack as unpack
import flyable.data.attribute
import flyable.data.attribute as _attribute
import flyable.data.comp_data as comp_data
import flyable.data.lang_func as lang_func
import flyable.data.lang_type as lang_type
import flyable.data.type_hint as hint
import flyable.parse.build_in as build
from flyable.code_gen import function
from flyable.parse.variable import Variable
import flyable.code_gen.code_gen as _gen
from flyable.data.lang_type import LangType, code_type, get_none_type
from flyable.code_gen.code_builder import CodeBuilder
from flyable.data.lang_func_impl import LangFuncImpl, FuncImplType

if TYPE_CHECKING:
    from flyable.parse.parser import Parser
    from flyable.code_gen.code_gen import CodeGen


class ParserVisitorAst(NodeVisitor):

    def __init__(self, parser, code_gen, func_impl):
        self.__code_gen: gen.CodeGen = code_gen
        self.__func = func_impl
        self.__parser = parser
        self.__data: comp_data.CompData = parser.get_data()
        self.__code_obj = None
        self.__bytecode = None
        self.__exception_entries = None
        self.__context = func_impl.get_context()
        self.__current_node = None

        self.__frame_ptr_value = 0

        self.__last_value = None
        self.__last_type = None

        self.__assign_type = None
        self.__assign_value = None

        self.__assign_depth = 0
        self.__out_blocks = []  # Hierarchy of blocks to jump when a context is over
        self.__cond_blocks = []  # Hierarchy of current blocks that might not get executed
        self.__exception_blocks = []  # Hierarchy of blocks to jump when an exception occur to dispatch it

    def run(self):
        self.__setup()

        self.visit(self.__func.get_parent_func().get_node())

        self.__builder.set_insert_block(self.__entry_block)
        self.__builder.br(self.__content_block)

        self.__code_gen.fill_not_terminated_block(self)

    def __setup(self):
        signature = self.__func.get_code_func_args_signature(self.__code_gen)
        code_func = self.__code_gen.get_or_create_func(self.__func.get_full_name(),
                                                       code_type.get_py_obj_ptr(self.__code_gen),
                                                       signature, _gen.Linkage.INTERNAL)

        self.__func.set_code_func(code_func)
        self.__entry_block = self.__func.get_code_func().add_block("Entry block")

        self.__builder = self.__func.get_code_func().get_builder()

        self.__content_block = self.__builder.create_block()
        self.__builder.set_insert_block(self.__content_block)

    def __setup_argument(self):
        callable_value = 0
        args_value = 1
        kwargs = 2
        if self.__func.get_impl_type() == FuncImplType.TP_CALL:
            for i, arg in enumerate(self.__func.get_parent_func().get_node().args.args):
                arg_var = self.get_or_gen_var(arg.arg)
                index = self.__builder.const_int64(i)
                item_ptr = gen_tuple.python_tuple_get_unsafe_item_ptr(self, lang_type.get_python_obj_type(), 1, index)
                arg_var.set_code_value(item_ptr)
        elif self.__func.get_impl_type() == FuncImplType.VEC_CALL:
            for i, arg in enumerate(self.__func.get_parent_func().get_node().args.args):
                arg_var = self.get_or_gen_var(arg.arg)
                item_ptr = self.__builder.gep2(args_value, code_type.get_py_obj_ptr(self.__code_gen),
                                               [self.__builder.const_int64(i)])
                arg_var.set_code_value(item_ptr)

    def visit(self, node):
        print(type(node))
        self.__current_node = node
        if isinstance(node, list):
            for e in node:
                super().visit(e)
            return

        if hasattr(node, "context") and node.context is None:
            return

        super().visit(node)

    def visit_node(self, node):
        return self.__visit_node(node)

    def __visit_node(self, node):
        self.visit(node)
        return self.__last_type, self.__last_value

    def visit_Assign(self, node: Assign) -> Any:
        self.__assign_depth += 1
        targets = []
        values = []

        if isinstance(node.targets[0], ast.Tuple) or isinstance(node.targets[0], ast.List):  # mult assign
            for e in node.targets[0].elts:
                targets.append(e)
        else:
            targets.append(node.targets)

        if isinstance(node.value, ast.Tuple) or isinstance(node.value, ast.List):
            for e in node.value.elts:
                values.append(e)
        else:
            values.append(node.value)

        if len(targets) == 1:  # Normal assign
            self.__assign_type, self.__assign_value = self.__visit_node(node.value)

            if not hint.is_incremented_type(self.__assign_type):
                ref_counter.ref_incr(self.__builder, self.__assign_type, self.__assign_value)
            hint.remove_hint_type(self.__assign_type, hint.TypeHintRefIncr)
            self.__reset_last()
            self.__last_type, self.__last_value = self.__visit_node(node.targets)
        else:  # Mult assign
            if len(targets) >= len(values):  # unpack
                value_type, value_value = self.__visit_node(node.value)
                unpack.unpack_assignation(self, targets, value_type, value_value, node)
            else:
                self.__parser.throw_error("Incorrect amount of value to unpack", node.lineno, node.end_col_offset)

        self.__reset_last()
        self.__assign_depth -= 1

    def visit_AnnAssign(self, node: AnnAssign) -> Any:
        self.__assign_depth += 1
        if node.value is not None:
            self.__assign_type, self.__assign_value = self.__visit_node(node.value)
            self.__reset_last()

            if not hint.is_incremented_type(self.__assign_type):
                ref_counter.ref_incr(self.__builder, self.__assign_type, self.__assign_value)
            hint.remove_hint_type(self.__assign_type, hint.TypeHintRefIncr)

            self.__last_type, self.__last_value = self.__visit_node(node.target)
            self.__reset_last()

        self.__assign_depth -= 1

    def visit_BinOp(self, node: BinOp) -> Any:
        left_type, left_value = self.__visit_node(node.left)
        self.__reset_last()
        right_type, right_value = self.__visit_node(node.right)
        self.__visit_node(node.op)

        op = op_call.get_binary_op_func_to_call(node.op)

        bin_func_to_call = self.__code_gen.get_or_create_func(op, code_type.get_py_obj_ptr(self.__code_gen),
                                                              [code_type.get_py_obj_ptr(self.__code_gen)] * 2,
                                                              _gen.Linkage.EXTERNAL)

        self.__last_type = lang_type.get_python_obj_type()
        self.__last_value = self.__builder.call(bin_func_to_call, [left_value, right_value])
        ref_counter.ref_decr_incr(self, left_type, left_value)
        ref_counter.ref_decr_incr(self, right_type, right_value)

    def visit_UnaryOp(self, node: UnaryOp) -> Any:
        value_type, value = self.__visit_node(node.operand)

        self.__last_type, self.__last_value = op_call.unary_op(self, value_type, value, node)
        ref_counter.ref_decr_incr(self, value_type, value)

    def visit_BoolOp(self, node: BoolOp) -> Any:
        types = []
        values = []
        for e in node.values:
            type, value = self.__visit_node(e)
            types.append(type)
            values.append(value)

        current_type = types[0]
        current_value = values[0]
        for i in range(1, len(types)):
            type_buffer, value_buffer = current_type, current_value
            current_type, current_value = op_call.bool_op(self, node.op, current_type, current_value, types[i],
                                                          values[i])
            ref_counter.ref_decr_incr(self, type_buffer, value_buffer)

        self.__last_type, self.__last_value = current_type, current_value

    def visit_Compare(self, node: Compare) -> Any:
        from flyable.parse.content.compare import parse_compare
        self.__last_type, self.__last_value = parse_compare(self, node)

    def visit_AugAssign(self, node: AugAssign) -> Any:
        import flyable.tool.token_change as token_change

        token_store = token_change.find_token_store(node)

        # Run what we can of the target. The visitor will stop if it finds a none context
        node.ctx = None
        base_type, base_value = self.__visit_node(node.target)

        # Load value first
        self.__last_type = base_type
        self.__last_value = base_value
        token_store.ctx = ast.Load()
        left_type, left_value = self.__visit_node(token_store)

        ref_counter.ref_incr(self.__builder, left_type, left_value)

        self.__reset_last()
        right_type, right_value = self.__visit_node(node.value)

        # Operate value and target together

        op = op_call.get_binary_aug_op_func_to_call(node.op)

        bin_func_to_call = self.__code_gen.get_or_create_func(op, code_type.get_py_obj_ptr(self.__code_gen),
                                                              [code_type.get_py_obj_ptr(self.__code_gen)] * 2,
                                                              _gen.Linkage.EXTERNAL)

        self.__assign_value = self.__builder.call(bin_func_to_call, [left_value, right_value])
        self.__assign_type = lang_type.get_python_obj_type()

        # And now do the assign
        self.__last_type = base_type
        self.__last_value = base_value
        token_store.ctx = ast.Store()
        self.__visit_node(token_store)

        # Decrement the left load if needed
        ref_counter.ref_decr_incr(self, left_type, left_value)

        # Decrement the right load if needed
        ref_counter.ref_decr_incr(self, right_type, right_value)

        # Increment the assignation if there is a need for it
        ref_counter.ref_incr(self.__builder, self.__assign_type, self.__assign_value)

    def visit_Expr(self, node: Expr) -> Any:
        # Represent an expression with the return value unused
        self.__reset_last()
        self.__last_type, self.__last_value = self.__visit_node(node.value)

        ref_counter.ref_decr_incr(self, self.__last_type, self.__last_value)

    def visit_Expression(self, node: Expression) -> Any:
        self.__reset_last()
        self.__last_type, self.__last_value = self.__visit_node(node.body)

    def visit_NamedExpr(self, node: NamedExpr) -> Any:
        self.__assign_type, self.__assign_value = self.__visit_node(node.value)
        self.__reset_last()
        self.__last_type, self.__last_value = self.__visit_node(node.target)

    def visit_arg(self, node: arg) -> Any:
        pass

    def visit_arguments(self, node: arguments) -> Any:
        pass

    def visit_Name(self, node: Name) -> Any:
        if isinstance(node.ctx, ast.Store):  # Store
            found_var = self.get_or_gen_var(node.id)
            value_type = self.__assign_type
            value = self.__assign_value
            if found_var is not None:  # store local
                self.__builder.store(value, found_var.get_code_value())
            else:  # Store global
                str_var = self.__code_gen.get_or_insert_str(node.id)
                str_var = self.__builder.global_var(str_var)
                str_var = self.__builder.load(str_var)
                val_type, val_value = runtime.value_to_pyobj(self, value, value_type)
                globals = function.py_function_get_globals(self, 0)
                gen_dict.python_dict_set_item(self, globals, str_var, val_value)
                ref_counter.ref_decr(self, value_type, value)
        else:  # Load
            self.__last_type = lang_type.get_python_obj_type()
            found_var = self.get_var(node.id)
            if found_var is None:
                # Var not found, so it's a global
                var_name = node.id
                self.__last_value = self.__get_global_obj(var_name)
            else:
                self.__last_value = self.__builder.load(found_var.get_code_value())

    def visit_Attribute(self, node: Attribute) -> Any:
        self.__reset_last()

        self.__last_type, self.__last_value = self.__visit_node(node.value)

        attr_name = self.__code_gen.get_or_insert_str(node.attr)
        attr_name = self.__builder.global_var(attr_name)
        attr_name = self.__builder.load(attr_name)

        get_attr = self.__code_gen.get_or_create_func("PyObject_GetAttr", code_type.get_py_obj_ptr(self.__code_gen),
                                                      [code_type.get_py_obj_ptr(self.__code_gen)] * 2,
                                                      _gen.Linkage.EXTERNAL)

        self.__last_value = self.__builder.call(get_attr, [self.__last_value, attr_name])
        self.__last_type = lang_type.get_python_obj_type()

    def visit_Call(self, node: Call) -> Any:
        if isinstance(node.func, ast.Attribute):
            self.__last_type, self.__last_value = self.__visit_node(node.func.value)
            call_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            call_name = node.func.id
        else:
            raise NotImplementedError("Call func node not supported")

        type_buffer = self.__last_type
        value_buffer = self.__last_value
        args_types = []
        args = []
        kwargs = {}

        for kw in node.keywords:
            self.__reset_last()
            key = ast.Constant()
            key.value = kw.arg

            _, key_value = self.__visit_node(key)
            _, value = self.__visit_node(kw.value)

            kwargs[key_value] = value

        for e in node.args:
            self.__reset_last()
            type, arg = self.__visit_node(e)
            args_types.append(type)
            args.append(arg)
            self.__last_type = None

        self.__last_type = type_buffer
        self.__last_value = value_buffer
        if self.__last_value is None:  # Calling a direct function, no method
            call = self.__get_global_obj(call_name)
            self.__last_type = lang_type.get_python_obj_type()
            self.__last_value = caller.call_callable(self, call, call, args, kwargs)
        else:  # Calling a possible method
            result_value = self.generate_entry_block_var(code_type.get_py_obj_ptr(self.__code_gen))
            found_attr = self.generate_entry_block_var(code_type.get_py_obj_ptr(self.__code_gen))
            str_var = self.__code_gen.get_or_insert_str(call_name)
            str_var = self.__builder.load(self.__builder.global_var(str_var))
            get_method_func = self.__code_gen.get_or_create_func("_PyObject_GetMethod",
                                                                 code_type.get_int32(),
                                                                 ([code_type.get_py_obj_ptr(self.__code_gen)] * 2) +
                                                                 [code_type.get_py_obj_ptr(
                                                                     self.__code_gen).get_ptr_to()],
                                                                 _gen.Linkage.EXTERNAL)
            is_method = self.__builder.call(get_method_func, [self.__last_value, str_var, found_attr])

            is_method_block = self.__builder.create_block()
            not_method_block = self.__builder.create_block()
            continue_block = self.__builder.create_block()

            is_method = self.__builder.ne(is_method, self.__builder.const_int32(0))
            self.__builder.cond_br(is_method, is_method_block, not_method_block)

            self.__builder.set_insert_block(is_method_block)
            # ref_counter.ref_incr(self.__builder, first_type, first_value)
            # ref_counter.ref_incr(self.__builder, second_type, second_value)
            value = caller.call_callable(self, self.__last_value, self.__builder.load(found_attr),
                                         [self.__last_value] + args, kwargs)
            self.__builder.store(value, result_value)
            self.__builder.br(continue_block)

            self.__builder.set_insert_block(not_method_block)
            # ref_counter.ref_incr(self.__builder, first_type, first_value)
            value = caller.call_callable(self, self.__last_value, self.__last_value, args, kwargs)
            self.__builder.store(value, result_value)
            self.__builder.br(continue_block)

            self.__builder.set_insert_block(continue_block)
            self.__last_type = lang_type.get_python_obj_type()
            self.__last_value = self.__builder.load(result_value)

    def visit_Subscript(self, node: Subscript) -> Any:
        pass

    def visit_Slice(self, node: Slice) -> Any:
        def parse_slice_part(expression: Optional[expr]):
            """Parses the slice part and returns the correct type and value"""
            if expression is not None:
                slice_part_type, slice_part_value = self.__visit_node(expression)
                slice_part_type, slice_part_value = runtime.value_to_pyobj(
                    self.__code_gen, self.__builder, slice_part_value, slice_part_type)
            else:
                slice_part_type = lang_type.get_none_type()
                slice_part_value = self.__builder.load(self.__builder.global_var(self.__code_gen.get_none()))
            return slice_part_type, slice_part_value

        lower_type, lower_value = parse_slice_part(node.lower)
        upper_type, upper_value = parse_slice_part(node.upper)
        step_type, step_value = parse_slice_part(node.step)

        self.__last_type = lang_type.get_python_obj_type()
        self.__last_value = gen_slice.py_slice_new(self, lower_value, upper_value, step_value)

    def visit_Delete(self, node: Delete) -> Any:
        for target in node.targets:
            self.__visit_node(target)

    def visit_Break(self, node: Break) -> Any:
        if len(self.__out_blocks) > 0:
            self.__builder.br(self.__out_blocks[-1])
        else:
            self.__parser.throw_error("'break' outside a loop", node.lineno, node.end_col_offset)

    def visit_Return(self, node: Return) -> Any:
        # If return is none, assumes a return type of None (which python does)
        if node.value is None:
            none_value = self.__builder.global_var(self.__code_gen.get_none())
            return_type, return_value = lang_type.get_python_obj_type(), self.__builder.load(none_value)
        else:
            return_type, return_value = self.__visit_node(node.value)

        ref_counter.ref_incr(self.__builder, return_type, return_value)

        ref_counter.decr_all_variables(self)

        conv_type, conv_value = runtime.value_to_pyobj(self, return_value, return_type)
        self.__builder.ret(conv_value)

    # FIXME: issues #39 & #41 and then complete the visitor
    def visit_Global(self, node: Global) -> Any:
        for name in node.names:
            local_var = self.get_or_gen_var(node)
            local_var.set_global(True)

    #  FIXME: issues #39 & #41 and then complete the visitor
    def visit_Nonlocal(self, node: Nonlocal) -> Any:
        for name in node.names:
            local_var = self.get_or_gen_var(node)
            local_var.set_global(True)

    def visit_Pass(self, node: Pass) -> Any:
        pass

    def visit_Constant(self, node: Constant) -> Any:
        if node.value is None:
            self.__last_type = lang_type.get_python_obj_type()
            self.__last_value = self.__builder.global_var(self.__code_gen.get_none())
        else:
            self.__last_type = lang_type.get_python_obj_type()
            constant_var = self.__code_gen.get_or_insert_const(node.value)
            self.__last_value = self.__builder.load(self.__builder.global_var(constant_var))

    def visit_IfExp(self, node: IfExp) -> Any:
        true_cond = self.__builder.create_block("If True")
        false_cond = self.__builder.create_block("If False")
        continue_cond = self.__builder.create_block("Continue If")

        test_type, test_value = self.__visit_node(node.test)
        self.__reset_last()

        cond_type, cond_value = cond.value_to_cond(self, test_type, test_value)
        self.__builder.cond_br(cond_value, true_cond, false_cond)

        # If true put the true value in the internal var
        self.__builder.set_insert_block(true_cond)
        true_type, true_value = self.__visit_node(node.body)
        self.__builder.br(continue_cond)
        self.__reset_last()

        # If false put the false value in the internal var
        self.__builder.set_insert_block(false_cond)
        false_type, false_value = self.__visit_node(node.orelse)

        common_type = lang_type.get_most_common_type(self.__data, true_type, false_type)
        new_var = self.generate_entry_block_var(common_type.to_code_type(self.__code_gen))

        self.__builder.set_insert_block(true_cond)
        true_value = self.__code_gen.convert_type(self.__builder, self.__code_gen, true_type, true_value, common_type)
        self.__builder.store(true_value, new_var)
        self.__builder.br(continue_cond)

        self.__builder.set_insert_block(false_cond)
        false_value = self.__code_gen.convert_type(self.__builder, self.__code_gen, false_type, false_value,
                                                   common_type)
        self.__builder.store(false_value, new_var)
        self.__builder.br(continue_cond)

        self.__builder.set_insert_block(continue_cond)
        self.__last_type = common_type
        self.__last_value = self.__builder.load(new_var)

    def visit_If(self, node: If) -> Any:
        block_go = self.__builder.create_block()
        block_continue = self.__builder.create_block()

        # If there is relevant info
        has_other_block = node.orelse is not None or (isinstance(node.orelse, list) and len(node.orelse) > 0)
        if has_other_block:
            other_block = self.__builder.create_block()

        cond_type_test, cond_value_test = self.__visit_node(node.test)

        cond_type, cond_value = cond.value_to_cond(self, cond_type_test, cond_value_test)

        ref_counter.ref_decr_incr(self, cond_type_test, cond_value_test)
        ref_counter.ref_decr_incr(self, cond_type, cond_value)

        if has_other_block:
            self.__builder.cond_br(cond_value, block_go, other_block)
        else:
            self.__builder.cond_br(cond_value, block_go, block_continue)

        self.__builder.set_insert_block(block_go)
        self.__visit_node(node.body)
        self.__builder.br(block_continue)

        if has_other_block:
            self.__builder.set_insert_block(other_block)
            self.__visit_node(node.orelse)
            self.__builder.br(block_continue)

        self.__builder.set_insert_block(block_continue)

    def visit_For(self, node: For) -> Any:
        block_for = self.__builder.create_block()
        block_for_in = self.__builder.create_block()
        block_else = self.__builder.create_block() if node.orelse is not None else None
        block_continue = self.__builder.create_block()

        iter_type, iter_value = self.visit_node(node.iter)

        ref_counter.ref_incr(self.__builder, iter_type, iter_value)

        if isinstance(node.target, ast.Name):
            name = node.target.id
            new_var = self.get_func().get_context().add_var(name, iter_type)
            alloca_value = self.generate_entry_block_var(iter_type.to_code_type(self.__code_gen))
            new_var.set_code_value(alloca_value)
        iterable_type, iterator = caller.call_obj(self, "__iter__", iter_value, iter_type, [], [], {})

        self.__builder.br(block_for)
        self.__builder.set_insert_block(block_for)

        next_type, next_value = caller.call_obj(self, "__next__", iterator, iterable_type, [], [], {})

        ref_counter.ref_incr(self.__builder, next_type, next_value)

        null_ptr = self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))

        test = self.__builder.eq(next_value, null_ptr)

        if node.orelse is None:
            self.__builder.cond_br(test, block_continue, block_for_in)
        else:
            self.__builder.cond_br(test, block_else, block_for_in)

        # Setup the for loop content
        self.__builder.set_insert_block(block_for_in)
        if isinstance(node.target, ast.Name):
            self.__builder.store(next_value, new_var.get_code_value())
        elif isinstance(node.target, ast.Tuple) or isinstance(node.target, ast.List):
            targets = []
            for t in node.target.elts:
                targets.append(t)
            unpack.unpack_assignation(self, targets, next_type, next_value, node)
        self.add_out_block(block_continue)  # In case of a break we want to jump after the for loop
        self.visit(node.body)
        ref_counter.ref_decr(self, next_type, next_value)
        self.pop_out_block()

        self.__builder.br(block_for)

        if node.orelse is not None:
            self.__builder.set_insert_block(block_else)
            excp.py_runtime_clear_error(self.__code_gen, self.__builder)
            self.visit(node.orelse)
            self.__builder.br(block_continue)

        self.__builder.set_insert_block(block_continue)
        ref_counter.ref_decr(self, iter_type, iter_value)
        excp.py_runtime_clear_error(self.__code_gen, self.__builder)

    def visit_While(self, node: While) -> Any:
        block_cond = self.__builder.create_block("Condition While")
        block_while_in = self.__builder.create_block("In While")
        block_else = self.__builder.create_block("Else While") if node.orelse is not None else None
        block_continue = self.__builder.create_block("After While")

        self.__builder.br(block_cond)
        self.__builder.set_insert_block(block_cond)

        test_type, test_value = self.__visit_node(node.test)
        cond_type, cond_value = cond.value_to_cond(self, test_type, test_value)

        ref_counter.ref_decr_incr(self, test_type, test_value)
        ref_counter.ref_decr_incr(self, cond_type, cond_value)

        if node.orelse is None:
            self.__builder.cond_br(cond_value, block_while_in, block_continue)
        else:
            self.__builder.cond_br(cond_value, block_while_in, block_else)

        # Setup the while loop content
        self.__builder.set_insert_block(block_while_in)
        self.__out_blocks.append(block_continue)  # In case of a break we want to jump after the while loop
        self.__visit_node(node.body)
        self.__out_blocks.pop()
        self.__builder.br(block_cond)

        if node.orelse is not None:
            self.__builder.set_insert_block(block_else)
            self.__visit_node(node.orelse)
            self.__builder.br(block_continue)

        self.__builder.set_insert_block(block_continue)

    def visit_With(self, node: With) -> Any:
        items = node.items
        all_vars_with = []
        with_types = []
        for with_item in items:
            type, value = self.__visit_node(with_item.context_expr)
            with_types.append(type)
            if type.is_obj() or type.is_python_obj():
                if with_item.optional_vars is not None:
                    with_var = self.__func.get_context().add_var(str(with_item.optional_vars.id), type)
                    all_vars_with.append(with_var)
                    self.__builder.store(value, with_var.get_code_gen_value())
                else:
                    all_vars_with.append(None)

                # def __exit__(self, exc_type, exc_value, traceback)
                exit_args_type = [type] + ([lang_type.get_python_obj_type()] * 3)
                caller.call_obj(self, "__enter__", value, type, [value], [type], {})

                exit_values = [value] + ([self.__builder.const_null(code_type.get_int8_ptr())] * 3)
                caller.call_obj(self, "__exit__", value, type, exit_values, exit_args_type, {})
            else:
                self.__parser.throw_error("Type " + type.to_str(self.__data) +
                                          " can't be used in a with statement", node.lineno, node.end_col_offset)
        self.__visit_node(node.body)

        # After the with the var can't be accessed anymore
        for var in all_vars_with:
            if var is not None:
                var.set_use(False)

    def visit_comprehension(self, node: comprehension) -> Any:
        target_name = node.target.id
        iter_type, iter_value = self.__visit_node(node.iter)
        target_var = self.__func.get_context().add_var(target_name, iter_type)
        alloca_value = self.generate_entry_block_var(iter_type.to_code_type(self.__code_gen))
        target_var.set_code_gen_value(alloca_value)
        self.__last_type, self.__last_value = caller.call_obj(self, "__iter__", iter_value, iter_type, [iter_value],
                                                              [iter_type], {})

    def visit_ListComp(self, node: ListComp) -> Any:
        result_array = gen_list.instanciate_python_list(self.__code_gen, self.__builder, self.__builder.const_int64(0))

        block_continue = self.__builder.create_block()
        prev_for_block = None

        for i, e in enumerate(node.generators):
            iter_type, iter_value = self.__visit_node(e.iter)
            iterable_type, iterator = caller.call_obj(self, "__iter__", iter_value, iter_type, [], [], {})

            block_for = self.__builder.create_block()
            self.__builder.br(block_for)
            self.__builder.set_insert_block(block_for)

            next_type, next_value = caller.call_obj(self, "__next__", iterator, iterable_type, [], [], {})

            null_ptr = self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))
            excp.py_runtime_clear_error(self.__code_gen, self.__builder)

            test = self.__builder.eq(next_value, null_ptr)

            block_for_in = self.__builder.create_block()
            if i == 0:
                self.__builder.cond_br(test, block_continue, block_for_in)
            else:
                self.__builder.cond_br(test, prev_for_block, block_for_in)

            # inside for loop
            self.__builder.set_insert_block(block_for_in)

            if isinstance(e.target, ast.Name):
                name = e.target.id
                new_var = self.__func.get_context().add_var(name, iter_type)
                alloca_value = self.generate_entry_block_var(iter_type.to_code_type(self.__code_gen))
                new_var.set_code_gen_value(alloca_value)
                self.__builder.store(next_value, new_var.get_code_gen_value())
            elif isinstance(e.target, ast.Tuple) or isinstance(e.target, ast.List):
                targets = []
                for t in e.target.elts:
                    targets.append(t)
                unpack.unpack_assignation(self, targets, next_type, next_value, node)

            # validate that each if is true
            for j, test in enumerate(e.ifs):
                block_cond = self.__builder.create_block()
                cond_type_test, cond_value_test = self.__visit_node(test)
                cond_type, cond_value = cond.value_to_cond(self, cond_type_test, cond_value_test)
                self.__builder.cond_br(cond_value, block_cond, block_for)
                self.__builder.set_insert_block(block_cond)

            if i == len(node.generators) - 1:
                elt_type, elt_value = self.__visit_node(node.elt)
                py_obj_type, py_obj = runtime.value_to_pyobj(self.__code_gen, self.__builder, elt_value, elt_type)
                gen_list.python_list_append(self, result_array, py_obj_type, py_obj)
                self.__builder.br(block_for)

            prev_for_block = block_for

        self.__builder.set_insert_block(block_continue)
        self.__last_type = lang_type.get_list_of_python_obj_type()
        self.__last_value = result_array

    def visit_List(self, node: List) -> Any:
        elts_types = []
        elts_values = []
        common_type = None
        for e in node.elts:
            type, value = self.__visit_node(e)
            elts_types.append(type)
            elts_values.append(value)
            self.__last_value = None

        array = gen_list.instanciate_python_list(self.__code_gen, self.__builder,
                                                 self.__builder.const_int64(len(elts_values)))
        self.__last_value = array
        self.__last_type = lang_type.get_python_obj_type()

        for i, e in enumerate(elts_values):
            py_obj_type, py_obj = runtime.value_to_pyobj(self, e, elts_types[i])
            index = self.__builder.const_int64(i)
            gen_list.python_list_set(self, self.__last_value, index, py_obj)
            ref_counter.ref_incr(self.__builder, py_obj_type, py_obj)

    def visit_Tuple(self, node: Tuple) -> Any:
        elts_types = []
        elts_values = []
        for e in node.elts:
            type, value = self.__visit_node(e)
            elts_types.append(type)
            elts_values.append(value)
            self.__last_value = None

        self.__last_type = lang_type.get_tuple_of_python_obj_type()
        new_tuple = gen_tuple.python_tuple_new(self.__code_gen, self.__builder,
                                               self.__builder.const_int64(len(elts_values)))
        self.__last_value = new_tuple
        self.__last_type.add_hint(hint.TypeHintRefIncr())

        for i, e in enumerate(elts_values):
            py_obj_type, py_obj = runtime.value_to_pyobj(self, e, elts_types[i])
            ref_counter.ref_incr(self.__builder, py_obj_type, py_obj)
            gen_tuple.python_tuple_set_unsafe(self, self.__last_value, i, py_obj)

    def visit_SetComp(self, node: SetComp) -> Any:
        null_value = self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))
        result_set = gen_set.instanciate_python_set(self, null_value)

        block_continue = self.__builder.create_block()
        prev_for_block = None

        for i, e in enumerate(node.generators):
            iter_type, iter_value = self.__visit_node(e.iter)
            iterable_type, iterator = caller.call_obj(self, "__iter__", iter_value, iter_type, [], [], {})

            block_for = self.__builder.create_block()
            self.__builder.br(block_for)
            self.__builder.set_insert_block(block_for)

            next_type, next_value = caller.call_obj(self, "__next__", iterator, iterable_type, [], [], {})

            null_ptr = self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))
            excp.py_runtime_clear_error(self.__code_gen, self.__builder)

            test = self.__builder.eq(next_value, null_ptr)

            block_for_in = self.__builder.create_block()
            if i == 0:
                self.__builder.cond_br(test, block_continue, block_for_in)
            else:
                self.__builder.cond_br(test, prev_for_block, block_for_in)

            # inside for loop
            self.__builder.set_insert_block(block_for_in)

            if isinstance(e.target, ast.Name):
                name = e.target.id
                new_var = self.__func.get_context().add_var(name, iter_type)
                alloca_value = self.generate_entry_block_var(iter_type.to_code_type(self.__code_gen))
                new_var.set_code_gen_value(alloca_value)
                self.__builder.store(next_value, new_var.get_code_gen_value())
            elif isinstance(e.target, ast.Tuple) or isinstance(e.target, ast.List):
                targets = []
                for t in e.target.elts:
                    targets.append(t)
                unpack.unpack_assignation(self, targets, next_type, next_value, node)

            # validate that each if is true
            for j, test in enumerate(e.ifs):
                block_cond = self.__builder.create_block()
                cond_type, cond_value = self.__visit_node(test)
                cond_type, cond_value = cond.value_to_cond(self, cond_type, cond_value)
                self.__builder.cond_br(cond_value, block_cond, block_for)
                self.__builder.set_insert_block(block_cond)

            if i == len(node.generators) - 1:
                elt_type, elt_value = self.__visit_node(node.elt)
                obj_to_set_type, obj_to_set_value = runtime.value_to_pyobj(self.__code_gen, self.__builder, elt_value,
                                                                           elt_type)
                gen_set.python_set_add(self, result_set, obj_to_set_value)
                self.__builder.br(block_for)

            prev_for_block = block_for

        self.__builder.set_insert_block(block_continue)
        self.__last_type = lang_type.get_set_of_python_obj_type()
        self.__last_value = result_set

    def visit_Set(self, node: Set) -> Any:
        set_type = lang_type.get_set_of_python_obj_type()
        null_value = self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))
        new_set = gen_set.instanciate_python_set(self, null_value)
        for e in node.elts:
            type, value = self.__visit_node(e)
            py_typ, py_obj = runtime.value_to_pyobj(self.__code_gen, self.__builder, value, type)
            gen_set.python_set_add(self, new_set, py_obj)
        self.__last_value = new_set
        self.__last_type = set_type
        self.__last_type.add_hint(hint.TypeHintRefIncr())

    def visit_DictComp(self, node: DictComp) -> Any:
        result_dict = gen_dict.python_dict_new(self)

        block_continue = self.__builder.create_block()
        prev_for_block = None

        for i, e in enumerate(node.generators):
            iter_type, iter_value = self.__visit_node(e.iter)

            iterable_type, iterator = caller.call_obj(self, "__iter__", iter_value, iter_type, [], [], {})

            block_for = self.__builder.create_block()
            self.__builder.br(block_for)
            self.__builder.set_insert_block(block_for)

            next_type, next_value = caller.call_obj(self, "__next__", iterator, iterable_type, [], [], {})

            null_ptr = self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))
            excp.py_runtime_clear_error(self.__code_gen, self.__builder)

            test = self.__builder.eq(next_value, null_ptr)

            block_for_in = self.__builder.create_block()
            if i == 0:
                self.__builder.cond_br(test, block_continue, block_for_in)
            else:
                self.__builder.cond_br(test, prev_for_block, block_for_in)

            # inside for loop
            self.__builder.set_insert_block(block_for_in)

            if isinstance(e.target, ast.Name):
                name = e.target.id
                new_var = self.__func.get_context().add_var(name, iter_type)
                alloca_value = self.generate_entry_block_var(iter_type.to_code_type(self.__code_gen))
                new_var.set_code_gen_value(alloca_value)
                self.__builder.store(next_value, new_var.get_code_gen_value())
            elif isinstance(e.target, ast.Tuple) or isinstance(e.target, ast.List):
                targets = []
                for t in e.target.elts:
                    targets.append(t)
                unpack.unpack_assignation(self, targets, next_type, next_value, node)

            # validate that each if is true
            for j, test in enumerate(e.ifs):
                block_cond = self.__builder.create_block()
                cond_type, cond_value = self.__visit_node(test)
                cond_type, cond_value = cond.value_to_cond(self, cond_type, cond_value)
                self.__builder.cond_br(cond_value, block_cond, block_for)
                self.__builder.set_insert_block(block_cond)

            if i == len(node.generators) - 1:
                key_type, key_value = self.__visit_node(node.key)
                value_type, value_value = self.__visit_node(node.value)
                obj_key_type, obj_key_value = runtime.value_to_pyobj(self.__code_gen, self.__builder, key_value,
                                                                     key_type)
                obj_value_type, obj_value_value = runtime.value_to_pyobj(self.__code_gen, self.__builder, value_value,
                                                                         value_type)
                gen_dict.python_dict_set_item(self, result_dict, obj_key_value, obj_value_value)
                self.__builder.br(block_for)

            prev_for_block = block_for

        self.__builder.set_insert_block(block_continue)
        self.__last_type = lang_type.get_dict_of_python_obj_type()
        self.__last_value = result_dict

    def visit_Dict(self, node: Dict) -> Any:
        new_dict = gen_dict.python_dict_new(self)
        for i, e in enumerate(node.values):
            key_type, key_value = self.__visit_node(node.keys[i])
            value_type, value_value = self.__visit_node(node.values[i])

            _, key_value = runtime.value_to_pyobj(self, key_value, key_type)
            _, value_value = runtime.value_to_pyobj(self, value_value, value_type)

            gen_dict.python_dict_set_item(self, new_dict, key_value, value_value)
            self.__last_value = None
        self.__last_value = new_dict
        self.__last_type = lang_type.get_dict_of_python_obj_type()

    def visit_Try(self, node: Try) -> Any:
        pass
        # import flyable.parse.content.content_try as content_try
        # content_try.parse_try(self, node)

    def visit_Raise(self, node: Raise) -> Any:
        self.__func.set_can_raise(True)  # There is a raise so it can raise an exception

        if node.cause is not None:
            self.__last_type, self.__last_value = self.__visit_node(node.cause)

        self.__last_type, self.__last_value = self.__visit_node(node.exc)

        excp.raise_exception(self, self.__last_value)

        excp.handle_raised_excp(self)

    def visit_Assert(self, node: Assert) -> Any:
        test_type, test_value = self.__visit_node(node.test)
        test_type, test_value = cond.value_to_cond(self, test_type, test_value)

        block_raise = self.__builder.create_block()
        block_continue = self.__builder.create_block()

        self.__builder.cond_br(test_value, block_continue, block_raise)

        self.__builder.set_insert_block(block_raise)
        self.__func.set_can_raise(True)

        if node.msg is not None:
            msg_type, msg_value = self.__visit_node(node.msg)
        else:
            msg_type = lang_type.get_python_obj_type()
            msg_type.add_hint(hint.TypeHintConstStr(""))
            msg_value = self.__builder.global_var(self.__code_gen.get_or_insert_str(""))
            msg_value = self.__builder.load(msg_value)

        msg_type, msg_value = runtime.value_to_pyobj(self.__code_gen, self.__builder, msg_value, msg_type)
        excp.raise_assert_error(self, msg_value)

        excp.raise_index_error(self)
        excp.handle_raised_excp(self)
        self.__builder.ret_null()

        self.__builder.set_insert_block(block_continue)

    def visit_Yield(self, node: Yield) -> Any:
        raise unsupported.FlyableUnsupported()

    def visit_YieldFrom(self, node: YieldFrom) -> Any:
        raise unsupported.FlyableUnsupported()

    def visit_Import(self, node: Import) -> Any:
        raise unsupported.FlyableUnsupported()

    def visit_ImportFrom(self, node: ImportFrom) -> Any:
        raise unsupported.FlyableUnsupported()

    def visit_ClassDef(self, node: ClassDef) -> Any:
        pass

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.visit(node.body)

    def get_code_gen(self):
        return self.__code_gen

    def get_builder(self):
        return self.__builder

    def get_data(self):
        return self.__data

    def get_parser(self):
        return self.__parser

    def get_current_node(self):
        return self.__current_node

    def get_func(self):
        return self.__func

    def get_except_block(self):
        if len(self.__exception_blocks) > 0:
            return self.__exception_blocks[-1]
        return None

    def get_entry_block(self):
        return self.__entry_block

    def generate_entry_block_var(self, code_type, need_to_be_nulled=False):
        current_block = self.__builder.get_current_block()
        self.__builder.set_insert_block(self.__entry_block)
        new_alloca = self.__builder.alloca(code_type)
        if need_to_be_nulled:
            self.__builder.store(self.__builder.const_null(code_type), new_alloca)
        self.__builder.set_insert_block(current_block)
        return new_alloca

    def add_except_block(self, block):
        self.__exception_blocks.append(block)

    def pop_except_block(self):
        return self.__exception_blocks.pop()

    def add_out_block(self, block):
        self.__out_blocks.append(block)

    def pop_out_block(self):
        self.__out_blocks.pop()

    def reset_last(self):
        self.__reset_last()

    def set_assign_type(self, assign_type):
        self.__assign_type = assign_type

    def set_assign_value(self, assign_value):
        self.__assign_value = assign_value

    def __reset_last(self):
        self.__last_type = None
        self.__last_value = None

    def __last_become_assign(self):
        self.__last_value = self.__assign_value
        self.__last_type = self.__assign_type

    def __setup_default_args(self):
        if isinstance(self.__func.get_parent_func().get_node(), ast.FunctionDef):  #
            args_count = self.__func.get_parent_func().get_args_count()
            default_args = self.__func.get_parent_func().get_node().args.defaults
            current = 0
            for i in range(args_count - len(default_args), args_count):
                arg_type, arg_value = self.__visit_node(default_args[current])
                new_var = self.__func.get_context().add_var(self.__func.get_parent_func().get_arg(i).arg, arg_type)
                new_var_alloca = self.generate_entry_block_var(arg_type.to_code_type(self.__code_gen))
                self.__builder.store(arg_value, new_var_alloca)
                new_var.set_code_gen_value(new_var_alloca)
                current += 1

    def __get_global_obj(self, name):
        import builtins
        if hasattr(builtins, name):
            dict_value = function.py_function_get_builtins(self, self.__frame_ptr_value)
        else:
            dict_value = function.py_function_get_globals(self, self.__frame_ptr_value)
        str_name_value = self.__builder.global_var(self.__code_gen.get_or_insert_str(name))
        str_name_value = self.__builder.load(str_name_value)
        return function.py_dict_get_item(self, dict_value, str_name_value)

    def get_or_gen_var(self, var_name: str | int):
        found_var = self.__context.get_var(var_name)
        if found_var is None:
            found_var = self.__context.add_var(var_name, lang_type.get_python_obj_type())
            found_var.set_code_value(self.generate_entry_block_var(code_type.get_py_obj_ptr(self.__code_gen)))
        return found_var

    def get_var(self, var_name):
        return self.__context.get_var_by_name(var_name)

    def __get_code_func(self):
        code_func = self.__func.get_code_func()
        if code_func is None:
            raise Exception(
                f"Could not instantiate ParserVisitor with function implementation {self.__func.get_id()}. Was the CodeFunc generated?")
        return code_func

    def __reset_info(self):
        self.__assign_type: LangType = LangType()
        self.__assign_value = None
        self.__last_type = LangType()
        self.__last_value = None
        self.__current_node = None
        self.__reset_visit = False

        self.__assign_depth = 0

        self.__out_blocks.clear()
        self.__cond_blocks.clear()
        self.__exception_blocks.clear()

        # Invalidate the codegen value of the variable
        for var in self.__func.get_context().vars_iter():
            var.set_code_gen_value(None)

        self.__get_code_func().clear_blocks()
        self.__entry_block = self.__get_code_func().add_block("Entry block")

        self.__builder.set_insert_block(self.__entry_block)

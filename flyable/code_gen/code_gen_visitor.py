import ast
from ast import *
from typing import Any
from flyable.code_gen.code_builder import CodeBuilder
from flyable.data.lang_func_impl import LangFuncImpl
from flyable.parse.node_info import *
import flyable.code_gen.runtime as runtime
import flyable.code_gen.caller as caller
import flyable.code_gen.code_type as code_type
import flyable.data.lang_type as lang_type
import flyable.code_gen.exception as excp
import flyable.code_gen.list as gen_list
import flyable.code_gen.dict as gen_dict
import flyable.code_gen.tuple as gen_tuple
import flyable.code_gen.op_call as op_call


class CodeGenVisitor(NodeVisitor):

    def __init__(self, code_gen, func_impl):
        entry_block = func_impl.get_code_func().add_block()
        self.__last_value = None
        self.__code_gen = code_gen
        self.__func: LangFuncImpl = func_impl
        self.__builder: CodeBuilder = func_impl.get_code_func().get_builder()
        self.__builder.set_insert_block(entry_block)

        self.__out_blocks = []  # Hierarchy of blocks to jump when a context is over
        self.__exception_blocks = []  # Hierarchy of blocks to jump when an exception occur to dispatch it

        self.__setup_initial_block()
        content_block = self.__builder.create_block()
        self.__builder.br(content_block)  # After variable alloca jump to the function content
        self.__builder.set_insert_block(content_block)

    def visit(self, node):
        if isinstance(node, list):
            for e in node:
                self.visit(e)
        else:
            super().visit(node)

    def __setup_initial_block(self):
        """
        All variables stack allocations are made in the entry block
        """
        for i, var in enumerate(self.__func.get_context().vars_iter()):
            if not var.is_arg():
                var_type = var.get_type().to_code_type(self.__code_gen.get_data())
                var.set_code_gen_value(self.__builder.alloca(var_type))
            else:
                var.set_code_gen_value(i)

    def __parse_node(self, node):
        self.visit(node)
        return self.__last_value

    def visit_Constant(self, node: Constant) -> Any:
        if isinstance(node.value, int):
            self.__last_value = self.__builder.const_int64(node.value)
        elif isinstance(node.value, float):
            self.__last_value = self.__builder.const_float64(node.value)
        elif isinstance(node.value, str):
            self.__last_value = self.__builder.global_var(self.__code_gen.get_or_insert_str(node.value))
            self.__last_value = self.__builder.load(self.__last_value)
        else:
            raise ValueError("Unsupported const node")

    def visit_Call(self, node: Call) -> Any:

        if isinstance(node.func, ast.Attribute):
            self.__last_value = self.__parse_node(node.func)

        args = []
        for e in node.args:
            args.append(self.__parse_node(e))
        info = self.__func.get_node_info(node)
        if isinstance(info, NodeInfoCallProc):
            self.__last_value = self.__builder.call(info.get_func().get_code_func(), args)
        elif isinstance(info, NodeInfoCallNewInstance):
            # TODO : Compute the size of the allocation
            self.__last_value = runtime.malloc_call(self.__code_gen, self.__builder, self.__builder.const_int64(100))
            ptr_type = type.LangType(type.LangType.Type.OBJECT, info.get_id())
            self.__last_value = self.__builder.ptr_cast(self.__last_value,
                                                        ptr_type.to_code_type(self.__code_gen.get_data()))

            func_impl_to_call = info.get_func_impl()
            if func_impl_to_call is not None:
                self.__builder.call(func_impl_to_call.get_code_func(),
                                    [self.__last_value] + args)  # Add the 'self' arg !
        elif isinstance(info, NodeInfoCallBuildIn):
            self.__last_value = info.get_func().codegen(args, self.__code_gen, self.__builder)
        elif isinstance(info, NodeInfoPyCall):
            name = info.get_name()
            args_types = [code_type.get_int8_ptr()] * len(args)
            self.__last_value = caller.call_obj(self.__code_gen, self.__builder, name, self.__last_value,
                                                lang_type.get_python_obj_type(), args, args_types)
            excp.py_runtime_print_error(self.__code_gen, self.__builder)
        else:
            raise NotImplementedError(str(info) + " Node info not implemented")

    def visit_Compare(self, node: Compare) -> Any:
        all = [node.left] + node.comparators
        last = None
        for e in range(len(node.ops)):
            first = self.__parse_node(all[e])
            second = self.__parse_node(all[e + 1])
            current_op = node.ops[e]
            if isinstance(current_op, ast.And):
                last = self.__builder.op_and(first, second)
            elif isinstance(current_op, ast.Or):
                last = self.__builder.op_or(first, second)
            elif isinstance(current_op, ast.Eq):
                last = self.__builder.eq(first, second)
            elif isinstance(current_op, ast.NotEq):
                last = self.__builder.ne(first, second)
            elif isinstance(current_op, ast.Lt):
                last = self.__builder.lt(first, second)
            elif isinstance(current_op, ast.LtE):
                last = self.__builder.lte(first, second)
            elif isinstance(current_op, ast.Gt):
                last = self.__builder.gt(first, second)
            elif isinstance(current_op, ast.GtE):
                last = self.__builder.gte(first, second)
            else:
                raise NotImplementedError("Compare op not supported")
        self.__last_value = last

    def visit_Name(self, node: Name) -> Any:
        info = self.__func.get_node_info(node)
        if isinstance(info, NodeInfoNameLocalVarCall):
            value = info.get_var().get_code_gen_value()
            if isinstance(node.ctx, ast.Load) and not info.get_var().is_arg():
                self.__last_value = self.__builder.load(value)
            else:
                self.__last_value = value
        else:
            raise NotImplementedError("Name case not supported")

    def visit_Attribute(self, node: Attribute) -> Any:
        info = self.__func.get_node_info(node)
        if isinstance(info, NodeInfoAttrCall):
            attr = info.get_attr().get_id()
        elif isinstance(info, NodeInfoPythonAttrCall):
            pass
        elif isinstance(info, NodeInfoNameLocalVarCall) and not info.get_var().is_arg():
            value = info.get_var().get_code_gen_value()
            if isinstance(node.ctx, ast.Load):
                self.__last_value = self.__builder.load(value)
            else:
                self.__last_value = value
        else:
            raise NotImplementedError("Name case not supported")

    def visit_If(self, node: If) -> Any:
        block_go = self.__builder.create_block()
        block_continue = self.__builder.create_block()

        self.__out_blocks.append(self.__builder.create_block())

        cond_value = self.__parse_node(node.test)
        self.__builder.cond_br(cond_value, block_go, block_continue)

        self.__builder.set_insert_block(block_go)
        self.visit(node.body)
        if self.__builder.get_current_block().needs_end():
            self.__builder.br(self.__out_blocks[-1])

        self.__builder.set_insert_block(block_continue)

        if isinstance(node.orelse, ast.If):  # elif right here
            self.visit(node.orelse)
            if self.__builder.get_current_block().needs_end():
                self.__builder.br(self.__out_blocks[-1])
        elif node.orelse is not None:  # Else statement here
            self.__parse_node(node.orelse)
            if self.__builder.get_current_block().needs_end():
                self.__builder.br(self.__out_blocks[-1])

        self.__builder.set_insert_block(self.__out_blocks[-1])
        self.__out_blocks.pop()

    def visit_For(self, node: For) -> Any:
        info = self.__func.get_node_info(node)
        if isinstance(info, NodeInfoFor):
            var = info.get_var()
            block_for = self.__builder.create_block()
            block_for_in = self.__builder.create_block()
            block_else = self.__builder.create_block() if node.orelse is not None else None
            block_continue = self.__builder.create_block()

            value = self.__parse_node(node.iter)
            iterator = caller.call_obj(self.__code_gen, self.__builder, "__iter__", value,
                                       lang_type.get_python_obj_type(), [], [])
            self.__builder.br(block_for)
            self.__builder.set_insert_block(block_for)

            next_value = caller.call_obj(self.__code_gen, self.__builder, "__next__", iterator,
                                         lang_type.get_python_obj_type(), [], [])

            self.__builder.store(next_value, var.get_code_gen_value())

            null_ptr = self.__builder.const_null(code_type.get_int8_ptr())

            test = self.__builder.eq(next_value, null_ptr)

            if node.orelse is None:
                self.__builder.cond_br(test, block_continue, block_for_in)
            else:
                self.__builder.cond_br(test, block_else, block_for_in)

            # Setup the for loop content
            self.__builder.set_insert_block(block_for_in)
            self.__out_blocks.append(block_continue)  # In case of a break we want to jump after the for loop
            self.__parse_node(node.body)
            self.__out_blocks.pop()
            self.__builder.br(block_for)

            if node.orelse is not None:
                self.__builder.set_insert_block(block_else)
                self.__parse_node(node.orelse)
                self.__builder.br(block_continue)

            self.__builder.set_insert_block(block_continue)

    def visit_While(self, node: While) -> Any:
        block_cond = self.__builder.create_block()
        block_while_in = self.__builder.create_block()
        block_else = self.__builder.create_block() if node.orelse is not None else None
        block_continue = self.__builder.create_block()

        self.__builder.br(block_cond)
        self.__builder.set_insert_block(block_cond)

        loop_value = self.__parse_node(node.test)

        if node.orelse is None:
            self.__builder.cond_br(loop_value, block_while_in, block_continue)
        else:
            self.__builder.cond_br(loop_value, block_while_in, block_else)

        # Setup the while loop content
        self.__builder.set_insert_block(block_while_in)
        self.__out_blocks.append(block_continue)  # In case of a break we want to jump after the while loop
        self.__parse_node(node.body)
        self.__out_blocks.pop()
        self.__builder.br(block_cond)

        if node.orelse is not None:
            self.__builder.set_insert_block(block_else)
            self.__parse_node(node.orelse)
            self.__builder.br(block_continue)

        self.__builder.set_insert_block(block_continue)

    def visit_Break(self, node: Break) -> Any:
        self.__builder.br(self.__out_blocks[-1])

    def visit_Return(self, node: Return) -> Any:
        if node.value is None:
            self.__builder.ret_void()
        else:
            self.__builder.ret(self.__parse_node(node.value))

    def visit_Expr(self, node: Expr) -> Any:
        self.__last_value = None
        super().visit(node)

    def visit_Expression(self, node: Expression) -> Any:
        super().visit_Expression(node)

    def visit_BinOp(self, node: BinOp) -> Any:
        left = self.__parse_node(node.left)
        right = self.__parse_node(node.right)
        result = None
        if isinstance(node.op, Add):
            result = self.__builder.add(left, right)
        elif isinstance(node.op, Sub):
            result = self.__builder.sub(left, right)
        elif isinstance(node.op, Mult):
            result = self.__builder.mul(left, right)
        elif isinstance(node.op, Div):
            result = self.__builder.div(left, right)
        elif isinstance(node.op, FloorDiv):
            pass  # TODO: Support floor div
        else:
            raise ValueError("Unsupported Op " + str(node))
        self.__last_value = result

    def visit_UnaryOp(self, node: UnaryOp) -> Any:
        # TODO : Clean that up
        info = self.__func.get_node_info(node)
        if isinstance(info, NodeInfoUnary):
            value = self.__parse_node(node.operand)
            if not info.get_call_type().is_primitive():
                value = caller.call_obj(self.__code_gen, self.__builder, node.get_func_name(), value,
                                        info.get_call_type(), [], [])
            else:
                value = op_call.unary_op(self.__code_gen, self.__builder, info.get_call_type(), value, node.op)

            self.__last_value = value
        else:
            raise NotImplementedError()

    def visit_BoolOp(self, node: BoolOp) -> Any:
        self.visit_BinOp(node)

    def visit_Expr(self, node: Expr) -> Any:
        self.__last_type = None
        super().visit(node.value)

    def visit_IfExp(self, node: IfExp) -> Any:
        info = self.__func.get_node_info(node)
        if isinstance(info, NodeInfoIfExpr):
            var = info.get_var()
            true_cond = self.__builder.create_block()
            false_cond = self.__builder.create_block()
            continue_cond = self.__builder.create_block()

            value = self.__parse_node(node.test)
            self.__builder.cond_br(value, true_cond, false_cond)

            # If true put the true value in the returned variale
            self.__builder.set_insert_block(true_cond)
            value_true = self.__parse_node(node.body)
            self.__builder.store(value_true, var.get_code_gen_value())
            self.__builder.br(continue_cond)

            # If false put the false value in the returned variable
            self.__builder.set_insert_block(false_cond)
            value_false = self.__parse_node(node.orelse)
            self.__builder.store(value_false, var.get_code_gen_value())
            self.__builder.br(continue_cond)

            # And then the expression load the value to return it
            self.__builder.set_insert_block(continue_cond)
            self.__last_value = self.__builder.load(var.get_code_gen_value())  # Load the value containing the result

        else:
            raise NotImplementedError()

    def visit_Assign(self, node: Assign) -> Any:
        info = self.__func.get_node_info(node)
        if isinstance(info, NodeInfoAssignTupleTuple):
            targets_value = []
            values = []
            for target in node.targets[0].elts:
                targets_value.append(self.__parse_node(target))
            for value_assign in node.value.elts:
                values.append(self.__parse_node(value_assign))
            for i in range(len(targets_value)):
                self.__builder.store(values[i], targets_value[i])
        elif isinstance(info, NodeInfoAssignBasic):
            self.__builder.store(self.__parse_node(node.value), self.__parse_node(node.targets[0]))
        else:
            raise NotImplementedError()

    def visit_AugAssign(self, node: AugAssign) -> Any:
        to_assign = self.__parse_node(node.target)
        load_to_assign = self.__builder.load(to_assign)

        increment = self.__parse_node(node.value)

        if isinstance(node.op, ast.Add):
            result_to_store = self.__builder.add(load_to_assign, increment)
        elif isinstance(node.op, ast.Sub):
            result_to_store = self.__builder.sub(load_to_assign, increment)
        elif isinstance(node.op, ast.Mult):
            result_to_store = self.__builder.mul(load_to_assign, increment)
        elif isinstance(node.op, ast.Div):
            result_to_store = self.__builder.div(load_to_assign, increment)
        else:
            raise NotImplementedError("AugAssign op not supported")

        self.__builder.store(result_to_store, to_assign)

    def visit_comprehension(self, node: comprehension) -> Any:
        info = self.__func.get_node_info(node)
        if isinstance(info, NodeInfoComprehension):
            pass

    def visit_ListComp(self, node: ListComp) -> Any:
        list_result = gen_list.instanciate_pyton_list(self.__code_gen, self.__builder, self.__builder.const_int64(0))

        # self.__parse_node(node.)

        self.__last_value = list_result

    def visit_DictComp(self, node: DictComp) -> Any:
        dict_result = gen_dict.python_dict_new()

        self.__last_value = dict_result

    def visit_List(self, node: List) -> Any:
        values = []
        for e in node.elts:
            values.append(self.__parse_node(e))
            self.__last_value = None

        array = gen_list.instanciate_pyton_list(self.__code_gen, self.__builder,
                                                self.__builder.const_int64(len(values)))
        self.__last_value = array
        for i, e in enumerate(values):
            index = self.__builder.const_int64(i)
            gen_list.python_list_set(self.__code_gen, self.__builder, self.__last_value, index, e)

    def visit_Dict(self, node: Dict) -> Any:
        new_dict = gen_dict.python_dict_new(self.__code_gen, self.__builder)
        for i, e in enumerate(node.values):
            key = self.__parse_node(node.keys[i])
            value = self.__parse_node(node.values[i])
            gen_dict.python_dict_set_item(self.__code_gen, self.__builder, new_dict, key, value)
            self.__last_value = None
        self.__last_value = new_dict

    def visit_Tuple(self, node: Tuple) -> Any:
        values = []
        for e in node.elts:
            values.append(self.__parse_node(e))
            self.__last_value = None

        new_tuple = gen_tuple.python_tuple_new(self.__code_gen, self.__builder,
                                               self.__builder.const_int64(len(values)))
        self.__last_value = new_tuple
        for i, e in enumerate(values):
            index = self.__builder.const_int64(i)
            gen_tuple.python_tuple_set_unsafe(self.__code_gen, self.__builder, self.__last_value, index, e)

    def visit_With(self, node: With) -> Any:
        items = node.items
        info = self.__func.get_node_info(node)
        if isinstance(info, NodeInfoWith):
            all_vars = info.get_vars()
            types = info.get_with_types()
            for i, with_item in enumerate(items):
                value = self.__parse_node(with_item.context_expr)
                if all_vars[i] is not None:  # Assign the 'as'
                    self.__builder.store(value, all_vars[i].get_code_gen_value())
                caller.call_obj(self.__code_gen, self.__builder, "__enter__", value, types[i], [value], [types[i]])
        self.__parse_node(node.body)

        for i, with_item in enumerate(items):
            value = self.__parse_node(with_item.context_expr)
            exit_values = [value] + ([self.__builder.const_null(code_type.get_int8_ptr())] * 3)
            exit_args = [types[i]] + ([lang_type.get_python_obj_type()] * 3)
            caller.call_obj(self.__code_gen, self.__builder, "__exit__", value, types[i], exit_values, exit_args)

    def visit_Try(self, node: Try) -> Any:
        block_continue = self.__builder.create_block()
        try_block_dispatch = self.__builder.create_block()
        else_block = self.__builder.create_block() if node.orelse is None else None
        self.__exception_blocks.append(try_block_dispatch)

        self.__parse_node(node.body)
        if node.orelse is None:
            self.__builder.br(block_continue) # If no exception happened with jump on continue
        else:
            self.__builder.br(else_block)  # If no exception happened with jump on the else

        self.__exception_blocks.pop()

        if node.orelse is not None:
            self.__builder.set_insert_block(else_block)
            self.__parse_node(node.orelse)
            self.__builder.br(block_continue)

        self.__builder.set_insert_block(try_block_dispatch)

        except_bodies_blocks = [self.__builder.create_block() for block in node.handlers]
        except_cond_blocks = [self.__builder.create_block() for block in node.handlers]
        except_not_found = self.__builder.create_block()

        for i, handle in enumerate(node.handlers):

            self.__builder.set_insert_block(except_block[-1])
            self.__parse_node(handle)

        self.__builder.set_insert_block(block_continue)


    def visit_ExceptHandler(self, node: ExceptHandler) -> Any:
        self.__parse_node(node.body)

    def visit_Raise(self, node: Raise) -> Any:
        value = self.__parse_node(node.exc)
        if len(self.__exception_blocks) == 0:
            return_type = self.__func.get_return_type().to_code_type(self.__code_gen.get_data())
            self.__builder.ret(self.__builder.const_null(return_type))
        else:
            self.__builder.br(self.__exception_blocks[-1])

    def visit_Import(self, node: Import) -> Any:
        pass

    def visit_ImportFrom(self, node: ImportFrom) -> Any:
        pass

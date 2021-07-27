import ast
from ast import *
from typing import Any
from flyable.data.lang_type import *
import flyable.data.lang_type as lang_type
import flyable.data.lang_func_impl as func
import flyable.parse.op as op
import flyable.data.lang_class as lang_class
import flyable.data.lang_func as lang_func
import flyable.parse.adapter as adapter
import flyable.parse.build_in as build
import flyable.data.attribut
from flyable.data.lang_func_impl import LangFuncImpl
import flyable.data.comp_data as comp_data
from flyable.code_gen.code_builder import CodeBuilder
import flyable.code_gen.caller as caller
import flyable.code_gen.list as gen_list
import flyable.code_gen.set as gen_set
import flyable.code_gen.tuple as gen_tuple
import flyable.code_gen.dict as gen_dict
import flyable.code_gen.runtime as runtime
import enum
import flyable.code_gen.op_call as op_call
import flyable.data.lang_type as lang_type
import flyable.data.type_hint as hint
import flyable.code_gen.ref_counter as ref_counter
import flyable.tool.repr_visitor as repr_vis
import flyable.code_gen.exception as excp
import flyable.code_gen.cond as cond
import flyable.code_gen.code_gen as gen
import flyable.code_gen.fly_obj as fly_obj
import flyable.code_gen.module as gen_module


class ParserVisitMode(enum.IntEnum):
    DISCOVERY = 1,
    GENERAL = 2


class ParserVisitor(NodeVisitor):

    def __init__(self, parser, code_gen, func_impl):
        self.__mode = ParserVisitMode.GENERAL
        self.__code_gen: gen.CodeGen = code_gen
        self.__assign_type: LangType = LangType()
        self.__assign_value = None
        self.__last_type: LangType = LangType()
        self.__last_value = None
        self.__func: LangFuncImpl = func_impl
        self.__parser = parser
        self.__data: comp_data.CompData = parser.get_data()
        self.__current_node = None

        self.__assign_depth = 0

        self.__out_blocks = []  # Hierarchy of blocks to jump when a context is over
        self.__exception_blocks = []  # Hierarchy of blocks to jump when an exception occur to dispatch it

        self.__entry_block = func_impl.get_code_func().add_block()

        self.__builder: CodeBuilder = func_impl.get_code_func().get_builder()
        self.__builder.set_insert_block(self.__entry_block)

        # Setup argument as var
        for i, var in enumerate(self.__func.get_context().vars_iter()):
            if var.is_arg():
                var.set_code_gen_value(i)
                self.__func.get_code_func().increment_value()

        self.__content_block = self.__builder.create_block()
        self.__builder.set_insert_block(self.__content_block)

    def parse(self):
        self.__last_type = None
        self.visit(self.__func.get_parent_func().get_node().body)
        self.__parse_over()

    def __parse_over(self):
        # When parsing is done we can put the final br of the entry block
        self.__builder.set_insert_block(self.__entry_block)
        self.__builder.br(self.__content_block)

        self.__func.get_code_func().set_return_type(self.__func.get_return_type().to_code_type(self.__code_gen))
        self.__code_gen.fill_not_terminated_block(self.__func.get_code_func())

    def visit(self, node):
        self.__current_node = node
        if isinstance(node, list):
            for e in node:
                super().visit(e)
        else:
            super().visit(node)

    def __visit_node(self, node):
        self.visit(node)
        return self.__last_type, self.__last_value

    def visit_Assign(self, node: Assign) -> Any:
        self.__assign_depth += 1
        targets = []
        values = []

        if isinstance(node.targets[0], ast.Tuple):  # mult assign
            for e in node.targets[0].elts:
                targets.append(e)
        else:
            targets.append(node.targets)

        if isinstance(node.value, ast.Tuple):
            for e in node.value.elts:
                values.append(e)
        else:
            values.append(node.value)

        if len(targets) == 1:  # Normal assign
            self.__assign_type, self.__assign_value = self.__visit_node(node.value)
            self.__reset_last()
            self.__last_type, self.__last_value = self.__visit_node(node.targets)
        else:  # Mult assign
            if len(targets) == len(values):
                for i, e in enumerate(targets):
                    self.__reset_last()
                    self.__assign_type, self.__assign_value = self.__visit_node(values[i])
                    self.__reset_last()
                    value_type, value = self.__visit_node(targets[i])
            elif len(targets) > 1 and len(values) == 1:  # unpack
                raise NotImplementedError("Unpack assignation not implemented")
            else:
                self.__parser.throw_error("Incorrect amount of value to unpack", node.lineno, node.end_col_offset)

        self.__reset_last()

    def visit_BinOp(self, node: BinOp) -> Any:
        left_type, left_value = self.__visit_node(node.left)
        self.__last_type = None
        right_type, right_value = self.__visit_node(node.right)
        self.__visit_node(node.op)
        self.__last_type, self.__last_value = op_call.bin_op(self, node.op, left_type, left_value, right_type,
                                                             right_value)

    def visit_UnaryOp(self, node: UnaryOp) -> Any:
        value_type, value = self.__visit_node(node.operand)
        self.__last_type, self.__last_value = op_call.unary_op(self, value_type, value, node.op)

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
            current_type, current_value = op_call.bool_op(self, node.op, current_type, current_value, types[i],
                                                          values[i])
        self.__last_type, self.__last_value = current_type, current_value

    def visit_Compare(self, node: Compare) -> Any:
        all = [node.left] + node.comparators
        last_value = None
        last_type = None
        for e in range(len(node.ops)):
            first_type, first_value = self.__visit_node(all[e])
            second_type, second_value = self.__visit_node(all[e + 1])
            current_op = node.ops[e]
            last_type, last_value = op_call.cond_op(self, current_op, first_type, first_value, second_type,
                                                    second_value)
        self.__last_value = last_value
        self.__last_type = last_type

    def visit_AugAssign(self, node: AugAssign) -> Any:
        right_type, right_value = self.__visit_node(node.value)
        left_type, left_value = self.__visit_node(node.target)
        if not left_type == right_type:
            self.__parser.throw_error("Type " + left_type.to_str(self.__data) + " can't be assigned to type"
                                      + right_type.to_str(self.__data))

        if left_type.is_primitive():
            old_value = self.__builder.load(left_value)
            new_value = op_call.bin_op(self, node.op, left_type, old_value, right_type, right_value)
            self.__builder.store(new_value, left_value)
        else:
            raise NotImplementedError()

    def visit_Expr(self, node: Expr) -> Any:
        self.__last_type = None
        self.__last_value = None
        super().visit(node.value)

    def visit_Expression(self, node: Expression) -> Any:
        self.__last_type = None
        self.__last_type, self.__last_value = self.__visit_node(node.body)

    def visit_arg(self, node: arg) -> Any:
        pass

    def visit_arguments(self, node: arguments) -> Any:
        pass

    def visit_Name(self, node: Name) -> Any:
        # Name can represent multiple things
        # Is it a declared variable ?
        found_var = self.__find_active_var(node.id)
        if found_var is not None:
            self.__last_type = found_var.get_type()
            if found_var.is_global():
                self.__last_value = self.__builder.global_var(found_var.get_code_gen_value())
            else:
                self.__last_value = found_var.get_code_gen_value()
            if not found_var.is_arg():
                if isinstance(node.ctx, Store):
                    self.__builder.store(self.__assign_value, self.__last_value)
                    self.__last_become_assign()
                else:
                    self.__last_value = self.__builder.load(self.__last_value)
                    self.__last_type = found_var.get_type()
        elif build.get_build_in_name(node.id) is not None:  # An element in the build-in module
            self.__last_type = lang_type.get_python_obj_type()
            module = self.__builder.global_var(self.__code_gen.get_build_in_module())
            module = self.__builder.load(module)
            str_content = self.__code_gen.get_or_insert_str(node.id)
            str_content = self.__builder.load(self.__builder.global_var(str_content))
            self.__last_value = runtime.py_runtime_get_attr(self.__code_gen, self.__builder, module, str_content)
        elif isinstance(node.ctx, Store):  # not found so declaring a variable
            found_var = self.__func.get_context().add_var(node.id, self.__assign_type)
            if self.__func.get_parent_func().is_global():
                var_name = "@global@var" + self.__func.get_parent_func().get_file().get_path()
                new_global_var = gen.GlobalVar(var_name, self.__assign_type.to_code_type(self.__code_gen))
                found_var.set_code_gen_value(new_global_var)
                found_var.set_global(True)
                self.__code_gen.add_global_var(new_global_var)
                self.__builder.store(self.__assign_value, self.__builder.global_var(new_global_var))
                self.__last_become_assign()
            else:
                alloca_value = self.__generate_entry_block_var(self.__assign_type.to_code_type(self.__code_gen))
                found_var.set_code_gen_value(alloca_value)
                self.__builder.store(self.__assign_value, alloca_value)
                self.__last_value = found_var.get_code_gen_value()
            self.__last_type = found_var.get_type()
        else:
            self.__parser.throw_error("Undefined '" + node.id + "'", node.lineno, node.col_offset)

    def visit_Attribute(self, node: Attribute) -> Any:
        self.__reset_last()
        self.__last_type, self.__last_value = self.__visit_node(node.value)

        if self.__last_type.is_python_obj():  # Python obj attribute. Type is unknown
            self.__last_type = lang_type.get_python_obj_type()
            str_value = self.__builder.global_var(self.__code_gen.get_or_insert_str(node.attr))
            str_value = self.__builder.load(str_value)
            if isinstance(node.ctx, ast.Store):
                py_obj = runtime.value_to_pyobj(self.__code_gen, self.__builder, self.__assign_value,
                                                self.__assign_type)
                runtime.py_runtime_set_attr(self.__code_gen, self.__builder, self.__last_value, str_value, py_obj)
                self.__last_become_assign()
            else:
                self.__last_value = runtime.py_runtime_get_attr(self.__code_gen, self.__builder, self.__last_value,
                                                                str_value)
        elif self.__last_type.is_obj():  # Flyable obj. The attribute type might be known. GEP access for more speed
            attr = self.__data.get_class(self.__last_type.get_id()).get_attribute(node.attr)
            if attr is not None:  # We found the attribute
                first_index = self.__builder.const_int32(0)
                second_index = self.__builder.const_int32(fly_obj.get_obj_attribute_start_index() + attr.get_id())
                attr_index = self.__builder.gep(self.__last_value, first_index, second_index)
                if isinstance(node.ctx, ast.Store):
                    self.__builder.store(self.__assign_value, attr_index)
                    self.__last_become_assign()
                else:
                    self.__last_value = self.__builder.load(attr_index)
                    self.__last_type = attr.get_type()
            else:  # Attribut not found. It might be a declaration !
                if isinstance(node.ctx, ast.Store):
                    self.__data.set_changed(True)
                    new_attr = flyable.data.attribut.Attribut()
                    new_attr.set_name(node.attr)
                    new_attr.set_type(self.__assign_type)
                    self.__data.get_class(self.__last_type.get_id()).add_attribute(new_attr)
                    first_index = self.__builder.const_int32(0)
                    second_index = self.__builder.const_int32(
                        fly_obj.get_obj_attribute_start_index() + new_attr.get_id())
                    attr_index = self.__builder.gep(self.__last_value, first_index, second_index)
                    self.__builder.store(self.__assign_value, attr_index)
                    self.__last_become_assign()
                else:
                    self.__parser.throw_error("Attribut '" + node.attr + "' not declared", node.lineno,
                                              node.end_col_offset)
                self.__last_become_assign()
        else:
            str_error = self.__last_type.to_str(self.__data)
            self.__parser.throw_error("Attribut access unrecognized from " + str_error, node.lineno,
                                      node.end_col_offset)

    def visit_Call(self, node: Call) -> Any:
        type_buffer = self.__last_type
        args_types = []
        args = []
        for e in node.args:
            self.__reset_last()
            type, arg = self.__visit_node(e)
            args_types.append(type)
            args.append(arg)
            self.__last_type = None
        self.__last_type = type_buffer

        self.__reset_last()

        name_call = ""
        if isinstance(node.func, ast.Attribute):
            self.__last_type, self.__last_value = self.__visit_node(node.func.value)
            name_call = node.func.attr
        elif isinstance(node.func, ast.Name):
            name_call = node.func.id
        else:
            NotImplementedError("Call func node not supported")

        # A call from an existing variable, current module or build-in
        if self.__last_type is None or self.__last_type.is_module():
            build_in_func = build.get_build_in(name_call)
            if build_in_func is not None and self.__last_type is None:  # Build-in func call
                if isinstance(build_in_func, build.BuildInFunc):
                    self.__last_type, self.__last_value = build_in_func.parse(args_types, args, self.__code_gen,
                                                                              self.__builder)
                else:  # Call a non implemented build-in function
                    self.__last_type = lang_type.get_python_obj_type()
                    module = self.__builder.global_var(self.__code_gen.get_build_in_module())
                    module = self.__builder.load(module)
                    self.__last_type, self.__last_value = caller.call_obj(self, name_call, module,
                                                                          get_python_obj_type(), args, args_types)
            else:
                if self.__last_type is None:
                    file = self.__func.get_parent_func().get_file()
                else:
                    file = self.__data.get_file(self.__last_type.get_id())

                content = file.find_content(name_call)
                if isinstance(content, lang_class.LangClass):
                    # New instance class call
                    self.__last_type = lang_type.get_obj_type(content.get_id())
                    self.__last_value = fly_obj.allocate_flyable_instance(self, content)

                    # Call the constructor
                    args_types = [self.__last_type] + args_types
                    args = [self.__last_value] + args
                    args_call = [content.get_lang_type()] + args_types  # Add the self argument
                    caller.call_obj(self, "__init__", self.__last_value, self.__last_type, args, args_types, True)

                elif isinstance(content, lang_func.LangFunc):
                    # Func call
                    func_impl_to_call = adapter.adapt_func(content, args_types, self.__data, self.__parser)
                    if func_impl_to_call is not None:
                        if not func_impl_to_call.is_unknown():
                            self.__last_type = func_impl_to_call.get_return_type()
                        else:
                            self.__parser.throw_error("Impossible to resolve function" +
                                                      func_impl_to_call.get_parent_func().get_name(), node.lineno,
                                                      node.col_offset)
                        self.__last_value = self.__builder.call(func_impl_to_call.get_code_func(), args)
                    else:
                        self.__parser.throw_error("Function " + node.func.id + " not found", node.lineno,
                                                  node.end_col_offset)
                else:
                    self.__parser.throw_error("'" + name_call + "' unrecognized", node.lineno, node.end_col_offset)
        elif self.__last_type.is_python_obj() or self.__last_type.is_collection():  # Python call object
            self.__last_type, self.__last_value = caller.call_obj(self, name_call, self.__last_value, self.__last_type,
                                                                  [self.__last_value] + args,
                                                                  [self.__last_type] + args_types)
        elif self.__last_type.is_obj():
            _class = self.__data.get_class(self.__last_type.get_id())
            func_to_call = _class.get_func(name_call)
            if func_to_call is None:
                str_error = "Not method '" + name_call + "' found"
                self.__parser.throw_error(str_error, node.lineno, node.end_col_offset)
            else:
                method_args = [self.__last_value] + args
                method_args_types = [self.__last_type] + args_types
                self.__last_type, self.__last_value = caller.call_obj(self, name_call, self.__last_value,
                                                                      self.__last_type, method_args, method_args_types)
        else:
            str_error = "Call unrecognized with " + self.__last_type.to_str(self.__data)
            self.__parser.throw_error(str_error, node.lineno, node.end_col_offset)

    def visit_Subscript(self, node: Subscript) -> Any:
        value_type, value = self.__visit_node(node.value)
        index_type, index_value = self.__visit_node(node.slice)
        if value_type.is_primitive():
            self.__parser.throw_error("'[]' can't be used on a primitive type", node.lineno, node.end_col_offset)
        else:
            self.__last_type, self.__last_value = caller.call_obj(self, "__getitem__", value, value_type,
                                                                  [value, index_value], [value_type, index_type])

    def visit_Break(self, node: Break) -> Any:
        if len(self.__out_blocks) > 0:
            self.__builder.br(self.__out_blocks[-1])
        else:
            self.__parser.throw_error("'break' outside a loop", node.lineno, node.end_col_offset)

    def visit_Return(self, node: Return) -> Any:
        return_type, return_value = self.__visit_node(node.value)
        if self.__func.get_return_type().is_unknown():
            self.__func.set_return_type(return_type)
            if node.value is None:
                self.__builder.ret_void()
            else:
                self.__builder.ret(return_value)
        elif return_type == self.__func.get_return_type():
            self.__builder.ret(return_value)
        else:
            str_error = "Incompatible return type. Type " + self.__func.get_return_type().to_str(
                self.__data) + " expected instead of " + return_type.to_str(self.__data)
            self.__parser.throw_error(str_error, node.lineno, node.end_col_offset)

    def visit_Constant(self, node: Constant) -> Any:
        if isinstance(node.value, bool):
            self.__last_type = get_bool_type()
            self.__last_type.add_hint(hint.TypeHintConstBool(node.value))
            self.__last_value = self.__builder.const_int1(int(node.value))
        elif isinstance(node.value, int):
            self.__last_type = get_int_type()
            self.__last_value = self.__builder.const_int64(node.value)
            self.__last_type.add_hint(hint.TypeHintConstInt(node.value))
        elif isinstance(node.value, float):
            self.__last_type = get_dec_type()
            self.__last_type.add_hint(hint.TypeHintConstDec(node.value))
            self.__last_value = self.__builder.const_float64(node.value)
        elif isinstance(node.value, str):
            self.__last_type = get_python_obj_type()
            self.__last_type.add_hint(hint.TypeHintConstStr(node.value))
            self.__last_value = self.__builder.global_var(self.__code_gen.get_or_insert_str(node.value))
            self.__last_value = self.__builder.load(self.__last_value)
        elif node.value is None:
            self.__last_type = get_none_type()
            self.__last_value = self.__builder.const_int32(0)
        else:
            self.__parser.throw_error("Undefined '" + node.id + "'", node.lineno, node.col_offset)

    def visit_IfExp(self, node: IfExp) -> Any:
        true_cond = self.__builder.create_block()
        false_cond = self.__builder.create_block()
        continue_cond = self.__builder.create_block()

        test_type, test_value = self.__visit_node(node.test)
        self.__reset_last()

        self.__builder.cond_br(test_value, true_cond, false_cond)

        # If true put the true value in the internal var
        self.__builder.set_insert_block(true_cond)
        true_type, true_value = self.__visit_node(node.body)
        self.__reset_last()

        # If false put the false value in the internal var
        self.__builder.set_insert_block(false_cond)
        false_type, false_value = self.__visit_node(node.orelse)

        common_type = lang_type.get_type_common(self.__data, true_type, false_type)
        new_var = self.__generate_entry_block_var(common_type.to_code_type(self.__code_gen))

        self.__builder.set_insert_block(true_cond)
        true_value = self.__code_gen.convert_type(self.__builder, true_type, true_value, common_type)
        self.__builder.store(true_value, new_var)
        self.__builder.br(continue_cond)

        self.__builder.set_insert_block(false_cond)
        false_value = self.__code_gen.convert_type(self.__builder, false_type, false_value, common_type)
        self.__builder.store(false_value, new_var)
        self.__builder.br(continue_cond)

        self.__builder.set_insert_block(continue_cond)
        self.__last_type = common_type
        self.__last_value = self.__builder.load(new_var)

    def visit_If(self, node: If) -> Any:
        block_go = self.__builder.create_block()
        block_continue = self.__builder.create_block()

        cond_type, cond_value = self.__visit_node(node.test)
        cond_type, cond_value = cond.value_to_cond(self, cond_type, cond_value)
        self.__builder.cond_br(cond_value, block_go, block_continue)

        self.__builder.set_insert_block(block_go)
        self.__visit_node(node.body)
        if self.__builder.get_current_block().needs_end():
            self.__builder.br(block_continue)

        self.__builder.set_insert_block(block_continue)

        # If there is relevant info
        has_other_block = node.orelse is not None or (isinstance(node.orelse, list) and len(node.orelse) > 0)
        if has_other_block:
            other_block = self.__builder.create_block()
            if isinstance(node.orelse, ast.If):  # elif handle
                self.__visit_node(node.orelse)
                if self.__builder.get_current_block().needs_end():
                    self.__builder.br(other_block)
            else:  # Else statement
                self.__visit_node(node.orelse)
                if self.__builder.get_current_block().needs_end():
                    self.__builder.br(other_block)
            self.__builder.set_insert_block(other_block)
        else:
            self.__builder.set_insert_block(block_continue)

    def visit_For(self, node: For) -> Any:
        block_for = self.__builder.create_block()
        block_for_in = self.__builder.create_block()
        block_else = self.__builder.create_block() if node.orelse is not None else None
        block_continue = self.__builder.create_block()

        name = node.target.id
        iter_type, iter_value = self.__visit_node(node.iter)
        new_var = self.__func.get_context().add_var(name, iter_type)
        alloca_value = self.__generate_entry_block_var(iter_type.to_code_type(self.__code_gen))
        new_var.set_code_gen_value(alloca_value)
        iterable_type, iterator = caller.call_obj(self, "__iter__", iter_value, iter_type, [iter_value], [iter_type])
        self.__builder.br(block_for)
        self.__builder.set_insert_block(block_for)

        next_type, next_value = caller.call_obj(self, "__next__", iterator, iterable_type, [iter_value],
                                                [iterable_type])

        self.__builder.store(next_value, new_var.get_code_gen_value())

        null_ptr = self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))

        test = self.__builder.eq(next_value, null_ptr)

        if node.orelse is None:
            self.__builder.cond_br(test, block_continue, block_for_in)
        else:
            self.__builder.cond_br(test, block_else, block_for_in)

        # Setup the for loop content
        self.__builder.set_insert_block(block_for_in)
        self.__out_blocks.append(block_continue)  # In case of a break we want to jump after the for loop
        self.visit(node.body)
        self.__out_blocks.pop()
        self.__builder.br(block_for)

        if node.orelse is not None:
            self.__builder.set_insert_block(block_else)
            self.visit(node.orelse)
            self.__builder.br(block_continue)

        self.__builder.set_insert_block(block_continue)

    def visit_While(self, node: While) -> Any:
        block_cond = self.__builder.create_block()
        block_while_in = self.__builder.create_block()
        block_else = self.__builder.create_block() if node.orelse is not None else None
        block_continue = self.__builder.create_block()

        self.__builder.br(block_cond)
        self.__builder.set_insert_block(block_cond)

        loop_type, loop_value = self.__visit_node(node.test)

        if node.orelse is None:
            self.__builder.cond_br(loop_value, block_while_in, block_continue)
        else:
            self.__builder.cond_br(loop_value, block_while_in, block_else)

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
                caller.call_obj(self, "__enter__", value, type, [value], [type])

                exit_values = [value] + ([self.__builder.const_null(code_type.get_int8_ptr())] * 3)
                caller.call_obj(self, "__exit__", value, type, exit_values, exit_args_type)
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
        alloca_value = self.__generate_entry_block_var(iter_type.to_code_type(self.__code_gen))
        target_var.set_code_gen_value(alloca_value)
        self.__last_type, self.__last_value = caller.call_obj(self, "__iter__", iter_value, iter_type, [iter_value],
                                                              [iter_type])

    def visit_ListComp(self, node: ListComp) -> Any:
        result_array = gen_list.instanciate_pyton_list(self.__code_gen, self.__builder, self.__builder.const_int64(0))

        block_continue = self.__builder.create_block()
        prev_for_block = None

        for i, e in enumerate(node.generators):
            block_for = self.__builder.create_block()
            block_for_in = self.__builder.create_block()

            name = e.target.id
            iter_type, iter_value = self.__visit_node(e.iter)
            new_var = self.__func.get_context().add_var(name, iter_type)
            alloca_value = self.__generate_entry_block_var(iter_type.to_code_type(self.__code_gen))
            new_var.set_code_gen_value(alloca_value)
            iterable_type, iterator = caller.call_obj(self, "__iter__", iter_value, iter_type, [iter_value],
                                                      [iter_type])
            self.__builder.br(block_for)
            self.__builder.set_insert_block(block_for)

            next_type, next_value = caller.call_obj(self, "__next__", iterator, iterable_type, [iter_value],
                                                    [iterable_type])

            self.__builder.store(next_value, new_var.get_code_gen_value())

            null_ptr = self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))
            excp.py_runtime_clear_error(self.__code_gen, self.__builder)

            test = self.__builder.eq(next_value, null_ptr)

            if i == 0:
                self.__builder.cond_br(test, block_continue, block_for_in)
            else:
                self.__builder.cond_br(test, prev_for_block, block_for_in)

            # inside for loop
            self.__builder.set_insert_block(block_for_in)

            # validate that each if is true
            for j, test in enumerate(e.ifs):
                block_cond = self.__builder.create_block()
                cond_type, cond_value = self.__visit_node(test)
                cond_type, cond_value = cond.value_to_cond(self, cond_type, cond_value)
                self.__builder.cond_br(cond_value, block_cond, block_for)
                self.__builder.set_insert_block(block_cond)

            if i == len(node.generators) - 1:
                elt_type, elt_value = self.__visit_node(node.elt)
                obj_to_list = runtime.value_to_pyobj(self.__code_gen, self.__builder, elt_value, elt_type)
                gen_list.python_list_append(self.__code_gen, self.__builder, result_array, obj_to_list)
                self.__builder.br(block_for)

            prev_for_block = block_for

        self.__builder.set_insert_block(block_continue)
        self.__last_type = lang_type.get_list_of_python_obj_type()
        self.__last_value = result_array

    def visit_List(self, node: List) -> Any:
        elts_types = []
        elts_values = []
        for e in node.elts:
            type, value = self.__visit_node(e)
            elts_types.append(type)
            elts_values.append(value)
            self.__last_value = None

        self.__last_type = lang_type.get_python_obj_type()
        self.__last_type.add_dim(lang_type.LangType.Dimension.LIST)
        array = gen_list.instanciate_pyton_list(self.__code_gen, self.__builder,
                                                self.__builder.const_int64(len(elts_values)))
        self.__last_value = array

        for i, e in enumerate(elts_values):
            py_obj = runtime.value_to_pyobj(self.__code_gen, self.__builder, e, elts_types[i])
            index = self.__builder.const_int64(i)
            gen_list.python_list_set(self.__code_gen, self.__builder, self.__last_value, index, py_obj)

    def visit_Tuple(self, node: Tuple) -> Any:
        elts_types = []
        elts_values = []
        for e in node.elts:
            type, value = self.__visit_node(e)
            elts_types.append(type)
            elts_values.append(value)
            self.__last_value = None

        self.__last_type = lang_type.get_python_obj_type()
        self.__last_type.add_dim(lang_type.LangType.Dimension.TUPLE)
        new_tuple = gen_tuple.python_tuple_new(self.__code_gen, self.__builder,
                                               self.__builder.const_int64(len(elts_values)))
        self.__last_value = new_tuple

        for i, e in enumerate(elts_values):
            py_obj = runtime.value_to_pyobj(self.__code_gen, self.__builder, e, elts_types[i])
            index = self.__builder.const_int64(i)
            gen_tuple.python_tuple_set_unsafe(self.__code_gen, self.__builder, self.__last_value, index, py_obj)

    def visit_SetComp(self, node: SetComp) -> Any:
        null_value = self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))
        result_set = gen_set.instanciate_pyton_set(self.__code_gen, self.__builder, null_value)

        block_continue = self.__builder.create_block()
        prev_for_block = None

        for i, e in enumerate(node.generators):
            block_for = self.__builder.create_block()
            block_for_in = self.__builder.create_block()

            name = e.target.id
            iter_type, iter_value = self.__visit_node(e.iter)
            new_var = self.__func.get_context().add_var(name, iter_type)
            alloca_value = self.__generate_entry_block_var(iter_type.to_code_type(self.__code_gen))
            new_var.set_code_gen_value(alloca_value)
            iterable_type, iterator = caller.call_obj(self, "__iter__", iter_value, iter_type, [iter_value],
                                                      [iter_type])
            self.__builder.br(block_for)
            self.__builder.set_insert_block(block_for)

            next_type, next_value = caller.call_obj(self, "__next__", iterator, iterable_type, [iter_value],
                                                    [iterable_type])

            self.__builder.store(next_value, new_var.get_code_gen_value())

            null_ptr = self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))
            excp.py_runtime_clear_error(self.__code_gen, self.__builder)

            test = self.__builder.eq(next_value, null_ptr)

            if i == 0:
                self.__builder.cond_br(test, block_continue, block_for_in)
            else:
                self.__builder.cond_br(test, prev_for_block, block_for_in)

            # inside for loop
            self.__builder.set_insert_block(block_for_in)

            # validate that each if is true
            for j, test in enumerate(e.ifs):
                block_cond = self.__builder.create_block()
                cond_type, cond_value = self.__visit_node(test)
                cond_type, cond_value = cond.value_to_cond(self, cond_type, cond_value)
                self.__builder.cond_br(cond_value, block_cond, block_for)
                self.__builder.set_insert_block(block_cond)

            if i == len(node.generators) - 1:
                elt_type, elt_value = self.__visit_node(node.elt)
                obj_to_set = runtime.value_to_pyobj(self.__code_gen, self.__builder, elt_value, elt_type)
                gen_set.python_set_add(self.__code_gen, self.__builder, result_set, obj_to_set)
                self.__builder.br(block_for)

            prev_for_block = block_for

        self.__builder.set_insert_block(block_continue)
        self.__last_type = lang_type.get_set_of_python_obj_type()
        self.__last_value = result_set

    def visit_Set(self, node: Set) -> Any:
        set_type = lang_type.get_set_of_python_obj_type()
        set_type.add_dim(LangType.Dimension.SET)
        null_value = self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))
        new_set = gen_set.instanciate_pyton_set(self.__code_gen, self.__builder, null_value)
        for e in node.elts:
            type, value = self.__visit_node(e)
            py_obj = runtime.value_to_pyobj(self.__code_gen, self.__builder, value, type)
            gen_set.python_set_add(self.__code_gen, self.__builder, new_set, py_obj)
        self.__last_value = new_set
        self.__last_type = set_type

    def visit_DictComp(self, node: DictComp) -> Any:
        result_dict = gen_dict.python_dict_new(self.__code_gen, self.__builder)

        block_continue = self.__builder.create_block()
        prev_for_block = None

        for i, e in enumerate(node.generators):
            block_for = self.__builder.create_block()
            block_for_in = self.__builder.create_block()

            name = e.target.id
            iter_type, iter_value = self.__visit_node(e.iter)
            new_var = self.__func.get_context().add_var(name, iter_type)
            alloca_value = self.__generate_entry_block_var(iter_type.to_code_type(self.__code_gen))
            new_var.set_code_gen_value(alloca_value)
            iterable_type, iterator = caller.call_obj(self, "__iter__", iter_value, iter_type, [iter_value],
                                                      [iter_type])
            self.__builder.br(block_for)
            self.__builder.set_insert_block(block_for)

            next_type, next_value = caller.call_obj(self, "__next__", iterator, iterable_type, [iter_value],
                                                    [iterable_type])

            self.__builder.store(next_value, new_var.get_code_gen_value())

            null_ptr = self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))
            excp.py_runtime_clear_error(self.__code_gen, self.__builder)

            test = self.__builder.eq(next_value, null_ptr)

            if i == 0:
                self.__builder.cond_br(test, block_continue, block_for_in)
            else:
                self.__builder.cond_br(test, prev_for_block, block_for_in)

            # inside for loop
            self.__builder.set_insert_block(block_for_in)

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
                obj_key = runtime.value_to_pyobj(self.__code_gen, self.__builder, key_value, key_type)
                obj_value = runtime.value_to_pyobj(self.__code_gen, self.__builder, value_value, value_type)
                gen_dict.python_dict_set_item(self.__code_gen, self.__builder, result_dict, obj_key, obj_value)
                self.__builder.br(block_for)

            prev_for_block = block_for

        self.__builder.set_insert_block(block_continue)
        self.__last_type = lang_type.get_python_obj_type()
        self.__last_type.add_dim(lang_type.LangType.Dimension.DICT)
        self.__last_value = result_dict

    def visit_Dict(self, node: Dict) -> Any:
        new_dict = gen_dict.python_dict_new(self.__code_gen, self.__builder)
        for i, e in enumerate(node.values):
            key_type, key_value = self.__visit_node(node.keys[i])
            value_type, value_value = self.__visit_node(node.values[i])
            gen_dict.python_dict_set_item(self.__code_gen, self.__builder, new_dict, key_value, value_value)
            self.__last_value = None
        self.__last_value = new_dict
        self.__last_type = lang_type.get_python_obj_type()
        self.__last_type.add_dim(lang_type.LangType.Dimension.DICT)

    def visit_Try(self, node: Try) -> Any:
        continue_block = self.__builder.create_block()
        excp_block = self.__builder.create_block()
        excp_not_found_block = self.__builder.create_block()
        else_block = self.__builder.create_block() if node.orelse is not None else None
        self.__exception_blocks.append(excp_block)
        handlers_block = []
        handlers_cond_block = []
        for e in node.handlers:
            handlers_block.append(self.__builder.create_block())
            handlers_cond_block.append(self.__builder.create_block())

        self.__visit_node(node.body)

        self.__builder.br(handlers_cond_block[0])

        if node.orelse is None:
            self.__builder.br(continue_block)
        else:
            self.__builder.br(else_block)

        self.__builder.set_insert_block(excp_block)

        self.__builder.br(handlers_cond_block[0])

        for i, handler in enumerate(node.handlers):  # For each exception statement
            self.__reset_last()
            self.__builder.set_insert_block(handlers_cond_block[i])
            excp_value = excp.py_runtime_get_excp(self.__code_gen, self.__builder)
            excp_type = fly_obj.get_py_obj_type(self.__builder, excp_value)
            excp_type = self.__builder.ptr_cast(excp_value, code_type.get_py_obj_ptr(self.__code_gen))
            obj_type, obj_type_value = self.__visit_node(handler.type)
            type_match = self.__builder.eq(obj_type_value, excp_type)
            other_block = handlers_cond_block[i + 1] if i < len(node.handlers) - 1 else excp_not_found_block
            self.__builder.cond_br(type_match, handlers_block[i], other_block)
            self.__builder.br(continue_block)
            self.__builder.set_insert_block(handlers_block[i])
            self.__visit_node(handler.body)
            self.__builder.br(continue_block)

        # self.__visit_node(node.finalbody)

        if node.orelse is not None:
            self.__builder.set_insert_block(else_block)
            self.__visit_node(node.orelse)
            self.__builder.br(continue_block)

        self.__builder.set_insert_block(continue_block)

    def visit_Raise(self, node: Raise) -> Any:
        self.__func.set_can_raise(True)  # There is a raise so it can raise an exception
        self.__last_type, self.__last_value = self.__visit_node(node.exc)
        if node.cause is not None:
            self.__visit_node(node.cause)

    def visit_Import(self, node: Import) -> Any:
        for e in node.names:
            var_name = e.asname if e.asname is not None else e.name
            file = self.__data.get_file(e.name)
            if file is None:  # Python module
                module_type = lang_type.get_python_obj_type()  # A Python module
                content = gen_module.import_py_module(self.__code_gen, self.__builder, var_name)
            else:  # Flyable module
                module_type = lang_type.get_module_type(file.get_id())
                content = self.__builder.const_int32(file.get_id())

            module_code_type = module_type.to_code_type(self.__code_gen)
            module_store = None

            new_var = self.__func.get_context().add_var(var_name, module_type)
            if self.__func.get_parent_func().is_global():
                new_global_var = gen.GlobalVar("@flyable@global@module@" + var_name, module_code_type)
                new_var.set_global(True)
                new_var.set_code_gen_value(new_global_var)
                self.__code_gen.add_global_var(new_global_var)
                module_store = self.__builder.global_var(new_global_var)
            else:
                new_var_value = self.__generate_entry_block_var(module_code_type)
                new_var.set_code_gen_value(new_var_value)
                module_store = new_var_value
            self.__builder.store(content, module_store)

    def visit_ImportFrom(self, node: ImportFrom) -> Any:
        name = node.module
        for e in node.names:
            var_name = (e.asname if e.asname is not None else e.name) + name
            file = self.__data.get_file(e.name)
            if file is None:  # Python module
                module_type = lang_type.get_python_obj_type()  # A Python module
                content = gen_module.import_py_module(self.__code_gen, self.__builder, var_name)
            else:  # Flyable module
                module_type = lang_type.get_module_type(file.get_id())
                content = self.__builder.const_int32(file.get_id())

            module_code_type = module_type.to_code_type(self.__code_gen)
            module_store = None

            new_var = self.__func.get_context().add_var(var_name, module_type)
            if self.__func.get_parent_func().is_global():
                new_global_var = gen.GlobalVar("@flyable@global@module@" + var_name, module_code_type)
                new_var.set_global(True)
                new_var.set_code_gen_value(new_global_var)
                self.__code_gen.add_global_var(new_global_var)
                module_store = self.__builder.global_var(new_global_var)
            else:
                new_var_value = self.__generate_entry_block_var(module_code_type)
                new_var.set_code_gen_value(new_var_value)
                module_store = new_var_value
            self.__builder.store(content, module_store)

    def visit_ClassDef(self, node: ClassDef) -> Any:
        pass

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        pass

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

    def __generate_entry_block_var(self, code_type):
        current_block = self.__builder.get_current_block()
        self.__builder.set_insert_block(self.__entry_block)
        new_alloca = self.__builder.alloca(code_type)
        self.__builder.set_insert_block(current_block)
        return new_alloca

    def __reset_last(self):
        self.__last_type = None
        self.__last_value = None

    def __last_become_assign(self):
        self.__last_value = self.__assign_value
        self.__last_type = self.__assign_type

    def __find_active_var(self, name):
        result = self.__func.get_context().find_active_var(name)
        if result is None:
            parent_func = self.__func.get_parent_func().get_file().get_global_func()
            if parent_func is not None:
                impl = parent_func.get_impl(1)
                result = impl.get_context().find_active_var(name)
        return result

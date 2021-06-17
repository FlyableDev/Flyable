import ast
from ast import *
from typing import Any
from flyable.data.lang_type import *
import flyable.data.lang_type as lang_type
import flyable.data.lang_func_impl as func
from flyable.parse.node_info import *
import flyable.parse.op as op
import flyable.data.lang_class as lang_class
import flyable.data.lang_func as lang_func
import flyable.parse.adapter as adapter
import flyable.parse.build_in as build
import flyable.data.attribut


class ParserVisitor(NodeVisitor):

    def __init__(self, parser, data):
        self.__data = data
        self.__assign_type: LangType = LangType()
        self.__last_type: LangType = LangType()
        self.__parser = parser
        self.__current_func: func.LangFuncImpl = None

    def parse(self, func_impl):
        self.__last_type = None
        self.__current_func = func_impl
        self.visit(func_impl.get_parent_func().get_node())

    def visit(self, node):
        if isinstance(node, list):
            for e in node:
                super().visit(e)
        else:
            super().visit(node)

    def __visit_node(self, node):
        self.visit(node)
        return self.__last_type

    def visit_Assign(self, node: Assign) -> Any:
        self.__last_type = None
        self.__assign_type = self.__visit_node(node.value)
        self.__last_type = None

        if not isinstance(node.targets[0], ast.Tuple):
            self.__current_func.set_node_info(node, NodeInfoAssignBasic())
        elif isinstance(node.targets[0], ast.Tuple) and (
                isinstance(node.value, ast.Tuple) or isinstance(node.value, ast.List)):
            self.__assign_type = self.__assign_type.get_content()
            self.__current_func.set_node_info(node, NodeInfoAssignTupleTuple())
            if len(node.targets[0].elts) != len(node.value.elts):
                self.__parser.throw_error("Amount of values to assign and to unpack doesn't match", node.lineno,
                                          node.end_col_offset)
        else:
            self.__current_func.set_node_info(node, NodeInfoAssignIter())

        for target in node.targets:
            target_type = self.__visit_node(target)
            self.__last_type = None
            if self.__assign_type != target_type:
                self.__parser.throw_error("Type "
                                          + self.__assign_type.to_str(self.__data) + " can't be assigned to type "
                                          + target_type.to_str(self.__data), node.lineno, node.end_col_offset)

    def visit_BinOp(self, node: BinOp) -> Any:
        left_type = self.__visit_node(node.left)
        self.__last_type = None
        right_type = self.__visit_node(node.right)
        if left_type.is_primitive():
            self.__current_func.set_node_info(node, NodeInfoOpPrimCall(left_type, right_type))
            self.__last_type = right_type
        elif left_type.is_python_obj():
            self.__current_func.set_node_info(node, NodeInfoOpPythonCall(op.get_op_func_call(node.op)))
            self.__last_type = type.get_python_obj_type()
        elif left_type.is_obj():
            raise NotImplementedError("Object operator not supported")
        elif left_type.is_unknown() is True:
            self.__last_type = type.get_unknown_type()
        else:
            self.__parser.throw_error("Operation not expected", node.lineno, node.col_offset)
        super().visit(node.op)

    def visit_UnaryOp(self, node: UnaryOp) -> Any:
        value_type = self.__visit_node(node.operand)
        op_name = op.get_op_func_call(node.op)
        self.__current_func.set_node_info(node, NodeInfoUnary(value_type, op_name))

        if value_type.is_primitive():
            # Not op return a boolean, the others return the same type
            if isinstance(node.op, ast.Not):
                self.__last_type = lang_type.get_bool_type()
            elif isinstance(node.op, ast.Invert):
                self.__last_type = lang_type.get_int_type()
            else:
                self.__last_type = value_type
        else:
            self.__last_type = adapter.adapt_call(op_name, value_type, [value_type], self.__data, self.__parser)

    def visit_BoolOp(self, node: BoolOp) -> Any:
        self.visit_BinOp(node)

    def visit_Compare(self, node: Compare) -> Any:
        initial_type = self.__visit_node(node.left)
        for e in node.comparators:
            self.__visit_node(e)
        self.__last_type = type.get_bool_type()

    def visit_AugAssign(self, node: AugAssign) -> Any:
        left_type = self.__visit_node(node.value)
        right_type = self.__visit_node(node.target)
        if not left_type == right_type:
            self.__parser.throw_error("Type " + left_type.to_str(self.__data) + " can't be assigned to type"
                                      + right_type.to_code_type(self.__data))

    def visit_Expr(self, node: Expr) -> Any:
        self.__last_type = None
        super().visit(node.value)

    def visit_Expression(self, node: Expression) -> Any:
        self.__last_type = None

    def visit_arg(self, node: arg) -> Any:
        pass

    def visit_Name(self, node: Name) -> Any:
        # Name can represent multiple things
        # Is it a declared variable ?
        if self.__current_func.get_context().find_active_var(node.id) is not None:
            found_var = self.__current_func.get_context().find_active_var(node.id)
            self.__last_type = found_var.get_type()
            self.__current_func.set_node_info(node, NodeInfoNameLocalVarCall(found_var))
        elif isinstance(node.ctx, Store):  # Declaring a variable
            found_var = self.__current_func.get_context().add_var(node.id, self.__assign_type)
            self.__current_func.set_node_info(node, NodeInfoNameLocalVarCall(found_var))
            self.__last_type = found_var.get_type()
        else:
            self.__parser.throw_error("Undefined '" + node.id + "'", node.lineno, node.col_offset)

    def visit_Attribute(self, node: Attribute) -> Any:

        if self.__last_type is None:  # Variable call
            # Is it a declared variable ?
            if self.__current_func.get_context().find_active_var(node.value.id) is not None:
                found_var = self.__current_func.get_context().find_active_var(node.value.id)
                self.__last_type = found_var.get_type()
                self.__current_func.set_node_info(node, NodeInfoNameLocalVarCall(found_var))
            elif isinstance(node.ctx, Store):  # Declaring a variable
                found_var = self.__current_func.get_context().add_var(node.value.id, self.__assign_type)
                self.__current_func.set_node_info(node, NodeInfoNameLocalVarCall(found_var))
                self.__last_type = found_var.get_type()
            else:
                self.__parser.throw_error("Undefined attribut '" + node.value.id + "'", node.lineno, node.col_offset)
        elif self.__last_type.is_python_obj():
            self.__last_type = type.get_python_obj_type()
        elif self.__last_type.is_obj():
            attr = self.__data.get_class(self.__last_type.get_id()).get_attribut(node.value)
            if attr is not None:
                self.__current_func.set_node_info(NodeInfoAttrCall(attr))
                self.__last_type = attr.get_type()
            else:  # Attribut not found. It might be a declaration !
                if isinstance(node.ctx, ast.Store):
                    self.__current_func.set_node_info(NodeInfoAttrCall(attr))
                    new_attr = flyable.data.attribut.Attribut()
                    new_attr.set_name(node.attr)
                    new_attr.set_type(self.__assign_type)
                    self.__data.get_class(self.__last_type.get_id()).add_attribute(new_attr)
                else:
                    self.__parser.throw_error("Attribut '" + node.value + "' not declared", node.lineno,
                                              node.end_col_offset)
        elif self.__last_type.is_python_obj():
            self.__current_func.set_node_info(node, NodeInfoPythonAttrCall(node.value.name))
            self.__last_type = type.get_python_obj_type()
        else:
            self.__parser.throw_error("Attribut access unrecognized")

    def visit_Call(self, node: Call) -> Any:

        type_buffer = self.__last_type
        args_types = []
        for e in node.args:
            args_types.append(self.__visit_node(e))
            self.__last_type = None
        self.__last_type = type_buffer

        name_call = ""
        if isinstance(node.func, ast.Attribute):
            self.__last_type = self.__visit_node(node.func)
            name_call = node.func.attr
        elif isinstance(node.func, ast.Name):
            name_call = node.func.id
        else:
            NotImplementedError("Call func node not supported")

        if self.__last_type is None or self.__last_type.is_module():  # A call from an existing variable, current module or build-in
            build_in_func = build.get_build_in(name_call)
            if build_in_func is not None and self.__last_type is None:  # Build-in func call
                build_in_func.parse(node, args_types, self.__parser)
                self.__last_type = build_in_func.get_type()
                self.__current_func.set_node_info(node, NodeInfoCallBuildIn(build_in_func))
            else:
                if self.__last_type is None:
                    file = self.__current_func.get_parent_func().get_file()
                else:
                    file = self.__data.get_file(self.__last_type.get_id())

                content = file.find_content(name_call)
                if isinstance(content, lang_class.LangClass):
                    # New instance class call
                    self.__last_type = type.get_obj_type(content.get_id())
                    constructor = content.get_func("__init__")
                    constructor_impl = None
                    if constructor is not None:
                        args_call = [content.get_lang_type()] + args_types  # Add the self argument
                        constructor_impl = adapter.adapt_func(constructor, args_call, self.__data, self.__parser)
                    self.__current_func.set_node_info(node, NodeInfoCallNewInstance(content.get_id(), constructor_impl))
                elif isinstance(content, lang_func.LangFunc):
                    # Func call
                    func_impl_to_call = adapter.adapt_func(content, args_types, self.__data, self.__parser)
                    if func_impl_to_call is not None:
                        if func_impl_to_call.is_unknown() == False:
                            self.__last_type = func_impl_to_call.get_return_type()
                            self.__current_func.set_node_info(node, NodeInfoCallProc(func_impl_to_call))
                        else:
                            self.__parser.throw_error("Impossible to resolve function" +
                                                      func_impl_to_call.get_parent_func().get_name(), node.lineno,
                                                      node.col_offset)
                    else:
                        self.__parser.throw_error("Function " + node.func.id + " not found", node.lineno,
                                                  node.end_col_offset)
                else:
                    self.__parser.throw_error("'" + name_call + "' unrecognized", node.lineno, node.end_col_offset)
        elif self.__last_type.is_python_obj():  # Python call object
            self.__current_func.set_node_info(node, NodeInfoPyCall(name_call))
            self.__last_type = type.get_python_obj_type()
        else:
            self.__parser.throw_error("Call unrecognized", node.lineno, node.end_col_offset)

    def visit_Return(self, node: Return) -> Any:
        return_type = self.__visit_node(node.value)
        if self.__current_func.get_return_type().is_unknown():
            self.__current_func.set_return_type(return_type)
        else:
            self.__parser.throw_error("Incompatible return type. Type " +
                                      self.__current_func.get_return_type().to_str(self.__data) +
                                      " expected instead of " +
                                      return_type.to_str(self.__data))

    def visit_Constant(self, node: Constant) -> Any:
        if isinstance(node.value, int):
            self.__last_type = get_int_type()
        elif isinstance(node.value, float):
            self.__last_type = get_dec_type()
        elif isinstance(node.value, bool):
            self.__last_type = get_bool_type()
        elif isinstance(node.value, str):
            self.__last_type = get_python_obj_type()
        else:
            self.__parser.throw_error("Undefined '" + node.id + "'", node.lineno, node.col_offset)

    def visit_IfExp(self, node: IfExp) -> Any:
        self.__visit_node(node.test)
        body_type = self.__visit_node(node.body)
        self.__visit_node(node.orelse)
        self.__last_type = body_type
        new_var = self.__current_func.get_context().add_var("@internal_var@", body_type)
        self.__current_func.set_node_info(node, NodeInfoIfExpr(new_var))

    def visit_If(self, node: If) -> Any:
        cond_type = self.__visit_node(node.test)
        if not cond_type == type.get_bool_type():
            self.__parser.throw_error("bool type expected for condition instead of " + cond_type.to_str(self.__data),
                                      node.lineno, node.end_col_offset)

        self.visit(node.body)
        if node.orelse is not None:
            self.visit(node.orelse)

    def visit_For(self, node: For) -> Any:
        name = node.target.id
        type_to_iter = self.__visit_node(node.iter)
        new_var = self.__current_func.get_context().add_var(name, type_to_iter)
        self.__current_func.set_node_info(node,NodeInfoFor(new_var))
        self.visit(node.body)
        if node.orelse is not None:
            self.visit(node.orelse)

    def visit_With(self, node: With) -> Any:
        items = node.items
        all_vars_with = []
        with_types = []
        for with_item in items:
            type = self.__visit_node(with_item.context_expr)
            with_types.append(type)
            if type.is_obj() or type.is_python_obj():
                if with_item.optional_vars is not None:
                    all_vars_with.append(
                        self.__current_func.get_context().add_var(str(with_item.optional_vars.id), type))
                else:
                    all_vars_with.append(None)

                if adapter.adapt_call("__enter__", type, [type], self.__data, self.__parser) is None:
                    self.__parser.throw_error("__enter__ implementation expected", node.lineno, node.end_col_offset)

                # def __exit__(self, exc_type, exc_value, traceback)
                exit_args_type = [type] + ([lang_type.get_python_obj_type()] * 3)

                if adapter.adapt_call("__exit__", type, exit_args_type, self.__data, self.__parser) is None:
                    self.__parser.throw_error("__exit__ implementation expected", node.lineno, node.end_col_offset)
            else:
                self.__parser.throw_error("Type " + type.to_str(self.__data) +
                                          " can't be used in a with statement", node.lineno, node.end_col_offset)
        self.__visit_node(node.body)

        # After the with the var can't be accessed anymore
        for var in all_vars_with:
            if var is not None:
                var.set_use(False)
        self.__current_func.set_node_info(node, NodeInfoWith(with_types, all_vars_with))

    def visit_comprehension(self, node: comprehension) -> Any:
        name = node.target.id
        type_to_iter = self.__visit_node(node.iter)
        iter_var = self.__current_func.get_context().add_var(name, type_to_iter)
        self.__current_func.set_node_info(node, NodeInfoComprehension(iter_var))
        if node.ifs is not None:
            self.__visit_node(node.ifs)
        self.__last_type = lang_type.get_python_obj_type()

    def visit_ListComp(self, node: ListComp) -> Any:
        for e in node.generators:
            self.__last_type = self.__visit_node(e)

        expr_type = self.__visit_node(node.elt)

        self.__last_type.add_dim(LangType.Dimension.LIST)

    def visit_List(self, node: List) -> Any:
        values = []
        for e in node.elts:
            values.append(self.__visit_node(e))
        self.__last_type = lang_type.get_python_obj_type()
        self.__last_type.add_dim(lang_type.LangType.Dimension.LIST)

    def visit_Tuple(self, node: Tuple) -> Any:
        for e in node.elts:
            self.__visit_node(e)
        self.__last_type = lang_type.get_python_obj_type()
        self.__last_type.add_dim(lang_type.LangType.Dimension.TUPLE)

    def visit_DictComp(self, node: DictComp) -> Any:
        pass

    def visit_Dict(self, node: Dict) -> Any:
        values = []
        keys = []
        for e in node.values:
            values.append(self.__visit_node(e))
        for e in node.keys:
            keys.append(self.__visit_node(e))
        self.__last_type = lang_type.get_python_obj_type()
        self.__last_type.add_dim(lang_type.LangType.Dimension.DICT)

    def visit_Import(self, node: Import) -> Any:
        for e in node.names:
            file = self.__data.get_file(e.name)
            if file is None:
                module_type = type.get_python_obj_type()  # A Python module
            else:
                module_type = type.get_module_type(file.get_id())
            new_var = self.__current_func.get_context().add_var(e.asname, module_type)
            self.__current_func.set_node_info(NodeInfoImportPythonModule(new_var))

    def visit_ImportFrom(self, node: ImportFrom) -> Any:
        # file = self.__data.get_file(node.module)
        raise NotImplementedError()

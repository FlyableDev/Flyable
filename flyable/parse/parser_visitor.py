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
        self.__assign_type = self.__visit_node(node.value)
        self.__last_type = None
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
        self.visit_BinOp(node)

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
            if self.__current_func.get_context().find_active_var(node.value) is not None:
                found_var = self.__current_func.get_context().find_active_var(node.value)
                self.__last_type = found_var.get_type()
                self.__current_func.set_node_info(node, NodeInfoNameLocalVarCall(found_var))
            elif isinstance(node.ctx, Store):  # Declaring a variable
                found_var = self.__current_func.get_context().add_var(node.value, self.__assign_type)
                self.__current_func.set_node_info(node, NodeInfoNameLocalVarCall(found_var))
                self.__last_type = found_var.get_type()
            else:
                self.__parser.throw_error("Undefined '" + node.value + "'", node.lineno, node.col_offset)
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

        if self.__last_type is None or self.__last_type.is_module():  # A call from an existing variable, current module or build-in
            build_in_func = build.get_build_in(node.func.id)
            if build_in_func is not None and self.__last_type is None:  # Build-in func call
                build_in_func.parse(node, args_types, self.__parser)
                self.__current_func.set_node_info(node, NodeInfoCallBuildIn(build_in_func))
            else:
                if self.__last_type is None:
                    file = self.__current_func.get_parent_func().get_file()
                else:
                    file = self.__data.get_file(self.__last_type.get_id())

                content = file.find_content(node.func.id)
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
                    self.__parser.throw_error("'" + node.func.id + "' unrecognized", node.lineno, node.end_col_offset)
        elif self.__last_type.is_python_obj():  # Python call object
            self.__current_func.set_node_info(NodeInfoPyCall(node.func.name))
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
        else:
            self.__parser.throw_error("Undefined '" + node.id + "'", node.lineno, node.col_offset)

    def visit_If(self, node: If) -> Any:
        cond_type = self.__visit_node(node.test)
        if not cond_type == type.get_bool_type():
            self.__parser.throw_error("bool type expected for condition instead of " + cond_type.to_str(self.__data),
                                      node.lineno, node.end_col_offset)

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
                    all_vars_with.append(self.__current_func.get_context().add_var(str(with_item.optional_vars.id), type))

                if adapter.adapt_call("__enter__", type, [type], self.__data, self.__parser) is None:
                    self.__parser.throw_error("__enter__ implementation expected", node.lineno, node.end_col_offset)

                # def __exit__(self, exc_type, exc_value, traceback)
                exit_args_type = [type] + ([lang_type.get_python_obj_type()] * 3)

                if adapter.adapt_call("__exit__", type, exit_args_type, self.__data, self.__parser) is None:
                    self.__parser.throw_error("__exit__ implementation expected", node.lineno, node.end_col_offset)
            else:
                self.__parser.throw_error("Type " + type.to_str(self.__data) +
                                          " can't be used in a with statement",node.lineno,node.end_col_offset)
        self.__visit_node(node.body)

        # After the with the var can't be accessed anymore
        for var in all_vars_with:
            var.set_use(False)
        self.__current_func.set_node_info(node, NodeInfoWith(with_types,all_vars_with))

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

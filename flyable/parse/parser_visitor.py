from __future__ import annotations

import ast
import copy
from ast import *
from typing import TYPE_CHECKING, Any, Union, TypeAlias, Generic, Type, Optional, TypeVar

import flyable.code_gen.caller as caller
import flyable.code_gen.code_gen as gen
import flyable.code_gen.cond as cond
import flyable.code_gen.debug as debug
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
import flyable.data.lang_class as lang_class
import flyable.data.lang_func as lang_func
import flyable.data.lang_type as lang_type
import flyable.data.type_hint as hint
import flyable.parse.adapter as adapter
import flyable.parse.build_in as build
from flyable.parse.variable import Variable
import flyable.code_gen.code_gen as _gen
from flyable.data.lang_type import LangType, code_type, get_none_type
from flyable.code_gen.code_builder import CodeBuilder
from flyable.data.lang_func_impl import LangFuncImpl

if TYPE_CHECKING:
    from flyable.parse.parser import Parser
    from flyable.code_gen.code_gen import CodeGen

AstSubclass = TypeVar('AstSubclass', bound=AST)

AstSubclassOrList = AstSubclass | list[AstSubclass]


class ParserVisitor(NodeVisitor, Generic[AstSubclass]):

    def __init__(self, parser: Parser, code_gen: CodeGen, func_impl: LangFuncImpl):
        self.__code_gen: gen.CodeGen = code_gen
        self.__assign_type: LangType = LangType()
        self.__assign_value = None
        self.__last_type: Union[LangType, None] = LangType()
        self.__last_value: int | None = None
        self.__aug_mode = False
        self.__func: LangFuncImpl = func_impl
        self.__parser = parser
        self.__data: comp_data.CompData = parser.get_data()
        self.__current_node: Optional[AstSubclass] = None
        self.__reset_visit = False

        self.__assign_depth = 0

        self.__out_blocks = []  # Hierarchy of blocks to jump when a context is over
        self.__cond_blocks = []  # Hierarchy of current blocks that might not get executed
        self.__exception_blocks = []  # Hierarchy of blocks to jump when an exception occur to dispatch it

        self.__get_code_func().clear_blocks()

        self.__entry_block = self.__get_code_func().add_block("Entry block")

        self.__builder: CodeBuilder = self.__get_code_func().get_builder()
        self.__builder.set_insert_block(self.__entry_block)

    def parse(self):
        self.__last_type = None
        self.__reset_visit = True
        while self.__reset_visit:
            self.__reset_info()
            self.__reset_visit = False
            self.__parse_begin()
            self.visit(self.__func.get_parent_func().get_node().body)
            self.__parse_over()

    def __parse_begin(self):

        self.__setup_default_args()

        # Setup argument as var

        impl_type = self.__func.get_impl_type()
        if impl_type == lang_func.FuncImplType.SPECIALIZATION:
            for i, var in enumerate(self.__func.get_context().vars_iter()):
                if var.is_arg():
                    var.set_code_gen_value(i)

        # For vec and tp functions, arguments are actually inside the array
        # We load them when we start the function
        # 1 is the codegen value of the list argument
        # If it's a method and we load the first argument from the callable object (id 0)
        is_method = self.__func.get_parent_func().get_class() is not None
        for i, var in enumerate(self.__func.get_context().vars_iter()):
            if var.is_arg():
                if (impl_type == lang_func.FuncImplType.TP_CALL or impl_type == lang_func.FuncImplType.VEC_CALL) \
                        and is_method and i == 0:
                    method_instance = self.__builder.ptr_cast(0, code_type.get_py_obj_ptr(
                        self.__code_gen).get_ptr_to())
                    self_ptr = self.__builder.gep2(method_instance, code_type.get_py_obj_ptr(self.__code_gen),
                                                   [self.__builder.const_int32(3)])
                    var.set_code_gen_value(self.__builder.load(self_ptr))
                elif impl_type == lang_func.FuncImplType.TP_CALL:
                    index_value = self.__builder.const_int32(i - 1 if is_method else i)
                    found_ptr = gen_list.python_list_array_get_item_unsafe(self,
                                                                           lang_type.get_list_of_python_obj_type(),
                                                                           1, index_value)
                    var.set_code_gen_value(found_ptr)
                elif impl_type == lang_func.FuncImplType.VEC_CALL:
                    index_value = self.__builder.const_int32(i - 1 if is_method else i)
                    found_ptr = self.__builder.gep2(1, code_type.get_py_obj_ptr(self.__code_gen), [index_value])
                    found_ptr = self.__builder.load(found_ptr)
                    var.set_code_gen_value(found_ptr)

        self.__content_block = self.__builder.create_block("Main Content")
        self.__builder.set_insert_block(self.__content_block)

    def __parse_over(self):
        # When parsing is done we can put the final br of the entry block
        self.__builder.set_insert_block(self.__entry_block)
        self.__builder.br(self.__content_block)

        self.__get_code_func().set_return_type(self.__func.get_return_type().to_code_type(self.__code_gen))
        self.__code_gen.fill_not_terminated_block(self)

        self.__func.set_parse_status(lang_func.LangFuncImpl.ParseStatus.ENDED)

    def visit(self, node: AstSubclassOrList):
        self.__current_node = node  # type: ignore
        if isinstance(node, list):
            for e in node:  # type: AstSubclass
                super().visit(e)
            return

        if hasattr(node, "context") and node.context is None:  # type: ignore
            return

        super().visit(node)

    def visit_node(self, node: AstSubclassOrList):
        return self.__visit_node(node)

    def __visit_node(self, node: AstSubclassOrList):
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
        self.__last_type, self.__last_value = op_call.bin_op(self, node.op, left_type, left_value, right_type,
                                                             right_value)
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
        self.__assign_type, self.__assign_value = op_call.bin_op(self, node.op, left_type, left_value, right_type,
                                                                 right_value)

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
        if not hint.is_incremented_type(self.__assign_type):
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
        # Name can represent multiple things
        # Is it a declared variable ?
        found_var = self.__find_active_var(node.id)
        if found_var is not None:
            if isinstance(found_var, gen.GlobalVar) and found_var.get_code_gen_value().belongs_to_module():
                # Imported module, retrieve stored global reference
                variable_reference = self.__builder.global_var(found_var.get_code_gen_value())
                self.__last_value = self.__builder.load(variable_reference)
                self.__last_type = copy.copy(found_var.get_type())
                self.__last_value = self.__builder.load(variable_reference)

                if self.__last_type.is_python_obj() and not found_var.is_module():
                    self.__last_type = lang_type.get_python_obj_type()
                    self.__last_type.add_hint(hint.TypeHintRefIncr())
                    self.__last_value = fly_obj.py_obj_get_attr(self, self.__last_value, found_var.get_name())
            elif isinstance(found_var, Variable) and found_var.belongs_to_module():
                self.__last_type = copy.deepcopy(found_var.get_type())
                self.__last_value = self.__builder.load(found_var.get_code_gen_value())

                if self.__last_type.is_python_obj() and not found_var.is_module():
                    self.__last_type = lang_type.get_python_obj_type()
                    self.__last_type.add_hint(hint.TypeHintRefIncr())
                    self.__last_value = fly_obj.py_obj_get_attr(self, self.__last_value, found_var.get_name())
            else:
                self.__last_type = found_var.get_type()
                if found_var.is_global():
                    self.__last_value = self.__builder.global_var(found_var.get_code_gen_value())
                else:
                    if found_var.get_code_gen_value() is None:
                        if not found_var.is_global():
                            found_var.set_code_gen_value(
                                self.generate_entry_block_var(found_var.get_type().to_code_type(self.__code_gen), True))

                    self.__last_value = found_var.get_code_gen_value()

                # Args don't live inside an alloca so they don't need to be loaded
                if not found_var.is_arg():
                    if isinstance(node.ctx, Store):
                        # If it tries to assign a global variable in a local context without the global keyword,
                        # instead declare a new local variable in the function context
                        if not found_var.is_global():
                            found_var = self.__func.get_context().add_var(node.id, self.__assign_type)
                            alloca_value = self.generate_entry_block_var(
                                self.__assign_type.to_code_type(self.__code_gen), True)
                            found_var.set_code_gen_value(alloca_value)
                            self.__builder.store(self.__assign_value, alloca_value)
                            self.__last_value = found_var.get_code_gen_value()
                            self.__last_type = copy.copy(found_var.get_type())
                            self.__last_type.add_hint(hint.TypeHintSourceLocalVariable(found_var))
                        # Else assign new value to variable
                        else:
                            # Decrement the old content
                            old_content = self.__builder.load(self.__last_value)
                            ref_counter.ref_decr_nullable(self, found_var.get_type(), old_content)

                            # The variable might have a new type
                            var_type = lang_type.get_most_common_type(self.__data, found_var.get_type(),
                                                                      self.__assign_type)
                            if found_var.get_type() != var_type:
                                found_var.set_type(var_type)
                                if found_var.is_global():
                                    self.__data.set_changed(True)
                                else:
                                    self.__reset_visit = True

                            # Store the new content
                            value_assign = self.__assign_value
                            if self.__last_type.is_python_obj():
                                _, value_assign = runtime.value_to_pyobj(self.__code_gen, self.__builder, value_assign,
                                                                         self.__assign_type)
                            hint.remove_hint_type(self.__last_type, hint.TypeHintConstInt)
                            self.__builder.store(value_assign, self.__last_value)
                            self.__last_become_assign()
                    else:
                        # if found_var.is_global() and found_var.get_context() != self.__func.get_context():
                        #    self.__parser.throw_error("Not found variable '" + node.id + "'", node.lineno, node.col_offset)
                        self.__last_value = self.__builder.load(self.__last_value)
                        self.__last_type = copy.copy(found_var.get_type())
                        self.__last_type.add_hint(hint.TypeHintSourceLocalVariable(found_var))
                else:
                    self.__last_value = found_var.get_code_gen_value()
                    self.__last_type = found_var.get_type()
        elif build.get_build_in_name(node.id) is not None:  # An element in the build-in module
            self.__last_type = lang_type.get_python_obj_type()
            module = self.__builder.global_var(self.__code_gen.get_build_in_module())
            module = self.__builder.load(module)
            self.__last_value = fly_obj.py_obj_get_attr(self, module, node.id)
        elif isinstance(node.ctx, Store):  # not found so declaring a variable
            found_var = self.__func.get_context().add_var(node.id, self.__assign_type)
            if self.__func.get_parent_func().is_global():
                var_name = f"@global@var@{found_var.get_name()}@{self.__func.get_parent_func().get_file().get_path()}"
                new_global_var = gen.GlobalVar(var_name, self.__assign_type.to_code_type(self.__code_gen))
                found_var.set_code_gen_value(new_global_var)
                found_var.set_global(True)
                self.__code_gen.add_global_var(new_global_var)
                self.__builder.store(self.__assign_value, self.__builder.global_var(new_global_var))
                self.__last_become_assign()
            else:
                alloca_value = self.generate_entry_block_var(self.__assign_type.to_code_type(self.__code_gen), True)
                found_var.set_code_gen_value(alloca_value)
                self.__builder.store(self.__assign_value, alloca_value)
                self.__last_value = found_var.get_code_gen_value()
            self.__last_type = copy.copy(found_var.get_type())
            self.__last_type.add_hint(hint.TypeHintSourceLocalVariable(found_var))
        else:
            self.__parser.throw_error("Undefined '" + node.id + "'", node.lineno, node.col_offset)

    def visit_Attribute(self, node: Attribute) -> Any:
        self.__reset_last()

        module_lookup = ""
        attributes = []
        node_copy = copy.deepcopy(node)

        while isinstance(node_copy, ast.Attribute):
            attributes.append(node_copy.attr)
            node_copy = node_copy.value

        if isinstance(node_copy, ast.Name):
            # This is a.b, not e.g. a().b
            attributes.append(node_copy.id)
            attributes.reverse()
            module_lookup = '.'.join(attributes)
        else:
            # need to get a in a().b
            self.visit(node_copy)

        # Because of how we store modules, let's condense this then search
        module_prefix = "@flyable@global@module@"
        module_name = module_prefix + module_lookup

        # check global imports
        module = self.__code_gen.get_global_var(module_name)
        
        # check local imports
        if not module:
            module = self.__find_active_var(module_lookup)
        
        node_copy.id = module_lookup

        if module is not None:
            # If we store the 'access level' module then we can return, no need to check the node attribute
            # e.g. "import os.path" results in us storing the module as "<module_prefix>os.path"
            # therefore, if we try to access this directly in the code then we can visit this node and return the module directly
            node_copy.id = module_lookup
            self.__last_type, self.__last_value = self.__visit_node(node_copy)
            return
        else:
            # It's still possible that this is a module access so:
            #   recursively check for an imported module for attribute access
            module_name = module_lookup
            for range_idx in range(len(attributes)):
                module_name = '.'.join(attributes[:range_idx - 1])
                global_module_lookup = module_prefix + module_name
                module = self.__code_gen.get_global_var(global_module_lookup)
                node_copy.id = module_name
                if module:
                    self.__last_type, self.__last_value = self.__visit_node(node_copy)
                    break
            if not module:
                # Access is not from an imported module, visit node value
                self.__last_type, self.__last_value = self.__visit_node(node.value)

        str_value = node.attr
        if self.__last_type.is_python_obj():  # Python obj attribute. Type is unknown
            self.__last_type = lang_type.get_python_obj_type()
            if isinstance(node.ctx, ast.Store):
                _, py_obj = runtime.value_to_pyobj(self.__code_gen, self.__builder, self.__assign_value,
                                                   self.__assign_type)
                fly_obj.py_obj_set_attr(self, self.__last_value, str_value, py_obj)
                self.__last_become_assign()
            elif isinstance(node.ctx, ast.Del):
                fly_obj.py_obj_del_attr(self, self.__last_value, str_value)
            else:
                self.__last_type.add_hint(hint.TypeHintRefIncr())
                self.__last_value = fly_obj.py_obj_get_attr(self, self.__last_value, str_value)
        elif self.__last_type.is_obj():  # Flyable obj. The attribute type might be known. GEP access for more speed
            attr = self.__data.get_class(self.__last_type.get_id()).get_attribute(str_value)
            if attr is not None:  # We found the attribute
                first_index = self.__builder.const_int32(0)
                second_index = self.__builder.const_int32(fly_obj.get_obj_attribute_start_index() + attr.get_id())
                attr_index = self.__builder.gep(self.__last_value, first_index, second_index)

                if isinstance(node.ctx, ast.Store):

                    common_type = lang_type.get_most_common_type(self.__data, attr.get_type(), self.__assign_type)
                    if attr.get_type() != common_type:  # Type mismatch between the attribute and the new assign
                        # Change the type of the attribute
                        attr.set_type(common_type)
                        self.__data.set_changed(True)  # Tell we changed an attribute to trigger a new compilation

                    if attr.get_type().is_python_obj():
                        self.__assign_type, self.__assign_value = runtime.value_to_pyobj(
                            self.__code_gen, self.__builder, self.__assign_value, self.__assign_type)

                    self.__builder.store(self.__assign_value, attr_index)
                    self.__last_become_assign()
                else:
                    self.__last_value = self.__builder.load(attr_index)
                    self.__last_type = copy.copy(attr.get_type())
                    self.__last_type.add_hint(hint.TypeHintSourceAttribute(attr))
            else:  # Attribute not found. It might be a declaration !
                if isinstance(node.ctx, ast.Store):
                    self.__data.set_changed(True)
                    new_attr = flyable.data.attribute.Attribut()
                    new_attr.set_name(node.attr)
                    new_attr.set_type(self.__assign_type)
                    self.__data.get_class(self.__last_type.get_id()).add_attribute(new_attr)
                    first_index = self.__builder.const_int32(0)
                    second_index = self.__builder.const_int32(
                        fly_obj.get_obj_attribute_start_index() + new_attr.get_id())
                    attr_index = self.__builder.gep(self.__last_value, first_index, second_index)

                    if new_attr.get_type().is_python_obj():
                        self.__assign_type, self.__assign_value = runtime.value_to_pyobj(
                            self.__code_gen, self.__builder, self.__assign_value, self.__assign_type)

                    self.__builder.store(self.__assign_value, attr_index)

                    self.__last_become_assign()
                else:
                    self.__parser.throw_error("Attribute '" + node.attr + "' not declared", node.lineno,
                                              node.end_col_offset)
                self.__last_become_assign()
        else:
            str_error = self.__last_type.to_str(self.__data)
            self.__parser.throw_error("Attribute " + str_value + " unrecognized from " + str_error, node.lineno,
                                      node.end_col_offset)

    def visit_Call(self, node: Call) -> Any:
        type_buffer = self.__last_type
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

        self.__reset_last()

        if isinstance(node.func, ast.Attribute):
            self.__last_type, self.__last_value = self.__visit_node(node.func.value)
            name_call = node.func.attr
        elif isinstance(node.func, ast.Name):
            name_call = node.func.id
        else:
            raise NotImplementedError("Call func node not supported")

        module_prefix = "@flyable@global@module@"
        module_global_func_name = module_prefix + name_call
        module_global_func_reference = self.__code_gen.get_global_var(module_global_func_name)

        if self.__last_type is None or self.__last_type.is_module():
            build_in_func = build.get_build_in(name_call)
            call_python_module = False
            if build_in_func is not None and self.__last_type is None:  # Build-in func call
                if isinstance(build_in_func, build.BuildInFunc):
                    type_values = build_in_func.parse(args_types, args, self)
                    if type_values is None:
                        call_python_module = True
                    else:
                        self.__last_type, self.__last_value = type_values
                else:
                    call_python_module = True

                if call_python_module:
                    self.__last_type = lang_type.get_python_obj_type()
                    module = self.__builder.global_var(self.__code_gen.get_build_in_module())
                    module = self.__builder.load(module)
                    self.__last_type, self.__last_value = caller.call_obj(self, name_call, module,
                                                                          lang_type.get_python_obj_type(), args,
                                                                          args_types, kwargs)
            elif module_global_func_reference or (self.__find_active_var(name_call) and self.__find_active_var(name_call).belongs_to_module()):
                # global module function
                node.func.id = name_call
                self.__last_type, self.__last_value = self.__visit_node(node.func)
                if self.__last_type.is_python_obj():
                    self.__last_type, self.__last_value = caller.call_obj(self, '__call__', self.__last_value,
                                                                          self.__last_type,
                                                                          args, args_types, kwargs)

            else:
                if self.__last_type is None:
                    file = self.__func.get_parent_func().get_file()
                else:
                    file = self.__data.get_file(self.__last_type.get_id())

                if file is None:
                    raise Exception("File of function called not found")

                content = file.find_content_by_name(name_call)

                if isinstance(content, lang_class.LangClass):
                    # New instance class call
                    self.__last_type = lang_type.get_obj_type(content.get_id())
                    self.__last_type.add_hint(hint.TypeHintRefIncr())
                    self.__last_value = fly_obj.allocate_flyable_instance(self, content)

                    # Call the constructor
                    caller.call_obj(self, "__init__", self.__last_value, self.__last_type, args, args_types, kwargs,
                                    True)

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
                        if func_impl_to_call.get_return_type().is_unknown():
                            self.__last_type = lang_type.get_none_type()
                            self.__last_value = self.__builder.const_int32(0)
                    else:
                        self.__parser.throw_error("Function " + node.func.id + " not found", node.lineno,
                                                  node.end_col_offset)
                elif content is None:
                    # If content is None, this could still be the __call__ method on a class
                    self.__last_type, self.__last_value = self.__visit_node(node.func)
                    calling_class = self.__data.get_class(self.__last_type.get_id())
                    method_name = "__call__"
                    func_to_call = calling_class.get_func(method_name)

                    if func_to_call is not None:
                        self.__last_type, self.__last_value = caller.call_obj(self, method_name, self.__last_value,
                                                                              self.__last_type, args, args_types,
                                                                              kwargs)
                        if self.__last_type.is_unknown():
                            self.__last_type = lang_type.get_none_type()
                            self.__last_value = self.__builder.const_int32(0)
                    else:
                        str_error = f"Method '{method_name}' not found"
                        self.__parser.throw_error(str_error, node.lineno, node.end_col_offset)
                else:
                    self.__parser.throw_error("'" + name_call + "' unrecognized", node.lineno, node.end_col_offset)
        elif self.__last_type.is_python_obj() or self.__last_type.is_collection():  # Python call object
            self.__last_type, self.__last_value = caller.call_obj(self, name_call, self.__last_value, self.__last_type,
                                                                  args, args_types, kwargs)
        elif self.__last_type.is_obj():
            _class = self.__data.get_class(self.__last_type.get_id())
            func_to_call = _class.get_func(name_call)
            if func_to_call is None:
                str_error = "Not method '" + name_call + "' found"
                self.__parser.throw_error(str_error, node.lineno, node.end_col_offset)
            else:
                self.__last_type, self.__last_value = caller.call_obj(self, name_call, self.__last_value,
                                                                      self.__last_type, args, args_types, kwargs)
                if self.__last_type.is_unknown():
                    self.__last_type = lang_type.get_none_type()
                    self.__last_value = self.__builder.const_int32(0)
        else:
            str_error = "Call unrecognized with " + self.__last_type.to_str(self.__data)
            self.__parser.throw_error(str_error, node.lineno, node.end_col_offset)

        self.__last_type.add_hint(hint.TypeHintRefIncr())
        ref_counter.ref_decr_multiple_incr(self, args_types, args)

    def visit_Subscript(self, node: Subscript) -> Any:
        value_type, value = self.__visit_node(node.value)

        index_type, index_value = self.__visit_node(node.slice)

        if isinstance(node.ctx, ast.Store):
            common_type = lang_type.get_most_common_type(self.__data, value_type, self.__assign_type)

            if common_type != value_type:
                if isinstance(value, Variable):
                    value.set_type(common_type)
                    if value.is_global():
                        self.__data.set_changed(True)  # A modification of global variable means recompile globally
                    else:
                        self.__reset_visit = True  # A new type for local variable means a local new code generation
                elif isinstance(value, _attribute.Attribute):
                    value.set_type(common_type)
                    self.__data.set_changed(True)  # Need to take in account the new type of the attribute

        args_types = [index_type]
        args = [index_value]

        if isinstance(node.ctx, ast.Store):
            func_name = "__setitem__"
            args_types += [self.__assign_type]
            args += [self.__assign_value]
        elif isinstance(node.ctx, ast.Del):
            func_name = "__delitem__"
        else:  # load
            func_name = "__getitem__"

        if value_type.is_primitive():
            self.__parser.throw_error("'[]' can't be used on a primitive type", node.lineno, node.end_col_offset)
        else:
            self.__last_type, self.__last_value = caller.call_obj(self, func_name, value, value_type, args, args_types,
                                                                  {})

        ref_counter.ref_decr_multiple_incr(self, args_types, args)

    def visit_Slice(self, node: Slice) -> Any:
        def parse_slice_part(expression: Optional[expr]):
            """Parses the slice part and returns the correct type and value"""
            if expression is not None:
                slice_part_type, slice_part_value = self.__visit_node(expression)
                slice_part_type, slice_part_value = runtime.value_to_pyobj(
                    self.__code_gen, self.__builder,
                    slice_part_value,
                    slice_part_type
                )
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
        # If return is void, assumes a return type of None (which python does)
        if node.value is None:
            return_type, return_value = lang_type.get_none_type(), self.__builder.const_int32(0)
        else:
            return_type, return_value = self.__visit_node(node.value)

        if not hint.is_incremented_type(return_type):  # Need to increment if we return to be consistent to CPython
            ref_counter.ref_incr(self.__builder, return_type, return_value)

        return_type.clear_hints()

        ref_counter.decr_all_variables(self)

        if self.__func.get_return_type().is_unknown():
            self.__func.set_return_type(return_type)
            self.__builder.ret(return_value)
        elif return_type == self.__func.get_return_type():
            self.__builder.ret(return_value)
        else:
            if not self.__func.get_return_type().is_python_obj():
                # We need to re-visit the function since we change the return type
                self.__func.set_return_type(lang_type.get_python_obj_type())
                self.__reset_visit = True
            conv_type, conv_value = runtime.value_to_pyobj(self.__code_gen, self.__builder, return_value, return_type)
            self.__builder.ret(conv_value)

    # FIXME: issues #39 & #41 and then complete the visitor
    def visit_Global(self, node: Global) -> Any:
        file = self.__func.get_parent_func().get_file()
        for name in node.names:
            global_var = self.__code_gen.get_global_var(f"@global@var@{name}@{file.get_path()}")
            _type = lang_type.from_code_type(global_var.get_type())
            local_var = self.__func.get_context().add_var(name, _type)
            local_var.set_code_gen_value(global_var)
            local_var.set_global(True)
            local_var.set_type(_type)

    #  FIXME: issues #39 & #41 and then complete the visitor
    def visit_Nonlocal(self, node: Nonlocal) -> Any:
        for name in node.names:
            self.__func.get_context()
            if self.__func.get_parent_func().is_global():
                pass

    def visit_Pass(self, node: Pass) -> Any:
        pass

    def visit_Constant(self, node: Constant) -> Any:
        if isinstance(node.value, bool):
            self.__last_type = lang_type.get_bool_type()
            self.__last_type.add_hint(hint.TypeHintConstBool(node.value))
            self.__last_value = self.__builder.const_int1(node.value)
            # self.__last_value = (
            #     self.__code_gen.get_true().get_id()
            #     if node.value
            #     else self.__code_gen.get_false().get_id()
            # )
        elif isinstance(node.value, int):
            self.__last_type = lang_type.get_int_type()
            self.__last_value = self.__builder.const_int64(node.value)
            self.__last_type.add_hint(hint.TypeHintConstInt(node.value))
        elif isinstance(node.value, float):
            self.__last_type = lang_type.get_dec_type()
            self.__last_type.add_hint(hint.TypeHintConstDec(node.value))
            self.__last_value = self.__builder.const_float64(node.value)
        elif isinstance(node.value, str):
            self.__last_type = lang_type.get_python_obj_type()
            self.__last_type.add_hint(hint.TypeHintConstStr(node.value))
            self.__last_value = self.__builder.global_var(self.__code_gen.get_or_insert_str(node.value))
            self.__last_value = self.__builder.load(self.__last_value)
        elif isinstance(node.value, bytes):
            self.__last_type = lang_type.get_python_obj_type()
            self.__last_type.add_hint(hint.TypeHintRefIncr())
            self.__last_value = flyable.code_gen.runtime.create_bytes_object(self.__code_gen, self.__builder,
                                                                             node.value)
        elif node.value is None:
            self.__last_type = lang_type.get_none_type()
            self.__last_value = self.__builder.const_int32(0)
        else:
            self.__parser.throw_error("Undefined '" + node.id + "'", node.lineno, node.col_offset)

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
        import flyable.parse.content.for_loop as for_loop
        for_loop.parse_for_loop(node, self)

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
            if common_type is None:
                common_type = type
            else:
                common_type = lang_type.get_most_common_type(self.__data, common_type, type)

        array = gen_list.instanciate_python_list(self.__code_gen, self.__builder,
                                                 self.__builder.const_int64(len(elts_values)))
        self.__last_value = array

        if common_type is None:
            self.__last_type = lang_type.get_list_of_python_obj_type()
        else:
            self.__last_type = lang_type.get_list_of_python_obj_type()
            for e in elts_types:
                self.__last_type.add_hint(hint.TypeHintCollectionContentHint(e))

        # Give the hints that specific that the returned new array is ref recounted
        self.__last_type.add_hint(hint.TypeHintRefIncr())

        for i, e in enumerate(elts_values):
            py_obj_type, py_obj = runtime.value_to_pyobj(self.__code_gen, self.__builder, e, elts_types[i])
            index = self.__builder.const_int64(i)
            gen_list.python_list_set(self, self.__last_value, index, py_obj)
            if not hint.is_incremented_type(py_obj_type):
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
            py_obj_type, py_obj = runtime.value_to_pyobj(self.__code_gen, self.__builder, e, elts_types[i])
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

            _, key_value = runtime.value_to_pyobj(self.__code_gen, self.__builder, key_value, key_type)
            _, value_value = runtime.value_to_pyobj(self.__code_gen, self.__builder, value_value, value_type)

            gen_dict.python_dict_set_item(self, new_dict, key_value, value_value)
            self.__last_value = None
        self.__last_value = new_dict
        self.__last_type = lang_type.get_dict_of_python_obj_type()

    def visit_Try(self, node: Try) -> Any:
        import flyable.parse.content.content_try as content_try
        content_try.parse_try(self, node)

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
        if not self.__func.has_yield():
            self.__func.set_yield(True)
            self.__reset_visit = True
        raise Exception("Yield not supported")

    def visit_YieldFrom(self, node: YieldFrom) -> Any:
        if not self.__func.has_yield():
            self.__func.set_yield(True)
            self.__reset_visit = True
        raise Exception("Yield not supported")

    def visit_Import(self, node: Import) -> Any:
        for e in node.names:
            import_name = e.asname or e.name
            import_names = import_name.split('.')
            import_hierarcy = 0
            for i in range(len(import_names)):
                to_import = '.'.join(import_names[:i+1])
                if self.__code_gen.get_global_var(f"@flyable@global@module@{to_import}"):
                    # module already imported
                    continue
                file = self.__data.get_file(to_import)
                if file is None:  # Python module
                    module_type = lang_type.get_python_obj_type()  # A Python module
                    content = gen_module.import_py_module(self.__code_gen, self.__builder, to_import)
                else:  # Flyable module
                    module_type = lang_type.get_module_type(file.get_id())
                    content = self.__builder.const_int32(file.get_id())

                module_code_type = module_type.to_code_type(self.__code_gen)

                new_var = self.__func.get_context().add_var(to_import, module_type)
                if self.__func.get_parent_func().is_global():
                    new_global_var = gen.GlobalVar("@flyable@global@module@" + to_import, module_code_type)
                    new_var.set_global(True)
                    new_var.set_code_gen_value(new_global_var)
                    self.__code_gen.add_global_var(new_global_var)
                    module_store = self.__builder.global_var(new_global_var)
                else:
                    new_var_value = self.generate_entry_block_var(module_code_type)
                    new_var.set_code_gen_value(new_var_value)
                    new_var.set_belongs_to_module(True)
                    new_var.set_is_module(True)
                    module_store = new_var_value
                self.__builder.store(content, module_store)

    def visit_ImportFrom(self, node: ImportFrom) -> Any:
        module_name = node.module
        for e in node.names:
            import_name = e.asname or e.name
            file = self.__data.get_file(e.name)
            if file is None:  # Python module
                module_type = lang_type.get_python_obj_type()  # A Python module
                content = gen_module.import_py_module(self.__code_gen, self.__builder, f"{module_name}")
            else:  # Flyable module
                module_type = lang_type.get_module_type(file.get_id())
                content = self.__builder.const_int32(file.get_id())

            module_code_type = module_type.to_code_type(self.__code_gen)

            new_var = self.__func.get_context().add_var(import_name, module_type)
            if self.__func.get_parent_func().is_global():
                new_global_var = gen.GlobalVar("@flyable@global@module@" + import_name, module_code_type,
                                               containing_module=module_name)
                new_var.set_global(True)
                new_var.set_code_gen_value(new_global_var)
                self.__code_gen.add_global_var(new_global_var)
                module_store = self.__builder.global_var(new_global_var)
            else:
                new_var_value = self.generate_entry_block_var(module_code_type)
                new_var.set_code_gen_value(new_var_value)
                new_var.set_belongs_to_module(True)
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

    def __find_active_var(self, name: str):
        result = self.__func.get_context().find_active_var(name)
        if isinstance(result, Variable) and result.is_global():
            parent_func = self.__func.get_parent_func().get_file().get_global_func()
            if parent_func is not None:
                impl = parent_func.get_impl(4)
                return impl.get_context().find_active_var(name)
        return result

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

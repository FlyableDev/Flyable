import flyable.code_gen.code_gen as gen

import flyable.data.comp_data as comp_data
import dis as dis
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as _gen
import flyable.code_gen.runtime as runtime
import flyable.code_gen.caller as caller
import flyable.code_gen.fly_obj as fly_obj
import flyable.code_gen.cond as _cond
import flyable.data.lang_type as lang_type


class ParserVisitor:

    def __init__(self, parser, code_gen, func_impl):
        self.__code_gen: gen.CodeGen = code_gen
        self.__func = func_impl
        self.__parser = parser
        self.__data: comp_data.CompData = parser.get_data()
        self.__code_obj = None
        self.__bytecode = None
        self.__context = func_impl.get_context()

        self.__jumps_instr = {}
        self.__instructions = []
        self.__entry_block = None
        self.__content_block = None
        self.__name = None  # Contains the value that contains the ptr to the name
        self.__consts = []
        self.__stack = []
        self.__blocks_stack = []
        self.__stack_states = []

    def run(self):
        self.__setup()
        self.__bytecode = dis.Bytecode(self.__func.get_parent_func().get_source_code())
        self.__bytecode = dis.Bytecode(self.__bytecode.codeobj.co_consts[0])
        self.__code_obj = self.__bytecode.codeobj

        self.__build_const()

        for instr in self.__bytecode:
            self.__instructions.append(instr)
            if instr.is_jump_target:
                new_block = self.__builder.create_block()
                self.__jumps_instr[instr] = new_block

        for instr in self.__instructions:
            self.__visit_instr(instr)

        self.__builder.set_insert_block(self.__entry_block)
        self.__builder.br(self.__content_block)

    def __visit_instr(self, instr):
        print(instr.opname)
        if instr in self.__jumps_instr:
            insert_block = self.__jumps_instr[instr]
            self.__builder.br(insert_block)
            self.__builder.set_insert_block(insert_block)

        method_to_visit = "visit_" + instr.opname.lower()
        if hasattr(self, method_to_visit):
            getattr(self, method_to_visit)(instr)
        else:
            raise Exception("Unsupported op " + instr.opname)

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

    def __build_const(self):
        for const_obj in self.__code_obj.co_consts:
            self.__consts.append(const_obj)

    def __gen_const(self, const_obj):
        if const_obj is None:
            new_const = self.__builder.global_var(self.__code_gen.get_none())
        elif isinstance(const_obj, str):
            new_const = self.__builder.global_var(self.__code_gen.get_or_insert_str(const_obj))
            new_const = self.__builder.load(new_const)
        elif isinstance(const_obj, bool):
            if const_obj:
                bool_var = self.__code_gen.get_true()
            else:
                bool_var = self.__code_gen.get_false()
            new_const = self.__builder.global_var(bool_var)
        elif isinstance(const_obj, int):
            const_value = self.__builder.const_int64(const_obj)
            new_const = runtime.value_to_pyobj(self.__code_gen, self.__builder, const_value,
                                               lang_type.get_int_type())
            new_const = new_const[1]
        elif isinstance(const_obj, tuple):
            pass
        elif type(const_obj).__name__ == "code":
            new_const = None
        else:
            raise Exception(
                "Not supported const of type " + str(type(const_obj)) + "with content " + str(const_obj))

    def visit_nop(self, instr):
        pass

    def visit_pop_top(self, instr):
        self.pop()

    def visit_rot_two(self, instr):
        buffer = self.__stack[-2]
        self.__stack[-2] = self.__stack[-1]
        self.__stack[-1] = buffer

    def visit_rot_three(self, instr):
        buffer = self.__stack[-1]
        self.__stack[-1] = self.__stack[-2]
        self.__stack[-2] = self.__stack[-3]
        self.__stack[-3] = buffer

    def visit_rot_four(self, instr):
        buffer = self.__stack[-1]
        self.__stack[-1] = self.__stack[-2]
        self.__stack[-2] = self.__stack[-3]
        self.__stack[-3] = self.__stack[-4]
        self.__stack[-4] = buffer

    def visit_dup_top(self, instr):
        self.__stack.append(self.__stack[-1])

    def visit_dup_top_two(self, instr):
        self.__stack.append(self.__stack[-2])
        self.__stack.append(self.__stack[-2])

    def visit_unary_positive(self, instr):
        value_type, value = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__pos__", value, value_type, [], [])
        self.push(new_value_type, new_value)

    def visit_unary_negative(self, instr):
        value_type, value = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__neg__", value, value_type, [], [])
        self.push(new_value_type, new_value)

    def visit_unary_not(self, instr):
        value_type, value = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__not__", value, value_type, [], [])
        self.push(new_value_type, new_value)

    def visit_unary_invert(self, instr):
        value_type, value = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__inv__", value, value_type, [], [])
        self.push(new_value_type, new_value)

    def visit_get_iter(self, instr):
        value_type, value = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__iter__", value, value_type, [], [])
        self.push(new_value_type, new_value)

    """"
    Binary opcode
    """

    def visit_binary_power(self, instr):
        value_type, value = self.pop()
        value_type_1, value_1 = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__pow__", value, value_type, [value_1], [value_type_1])
        self.push(new_value_type, new_value)

    def visit_binary_multiply(self, instr):
        value_type, value = self.pop()
        value_type_1, value_1 = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__mul__", value, value_type, [value_1], [value_type_1])
        self.push(new_value_type, new_value)

    def visit_binary_matrix_multiply(self, instr):
        raise NotImplementedError()
        value_type, value = self.pop()
        value_type_1, value_1 = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__pow__", value, value_type, [value_1], [value_type_1])
        self.push(new_value_type, new_value)

    def visit_binary_floor_divide(self, instr):
        value_type, value = self.pop()
        value_type_1, value_1 = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__floor_div__", value, value_type, [value_1],
                                                    [value_type_1])
        self.push(new_value_type, new_value)

    def visit_binary_true_divide(self, instr):
        value_type, value = self.pop()
        value_type_1, value_1 = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__div__", value, value_type, [value_1],
                                                    [value_type_1])
        self.push(new_value_type, new_value)

    def visit_binary_modulo(self, instr):
        value_type, value = self.pop()
        value_type_1, value_1 = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__mod__", value, value_type, [value_1],
                                                    [value_type_1])
        self.push(new_value_type, new_value)

    def visit_binary_add(self, instr):
        value_type, value = self.pop()
        value_type_1, value_1 = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__add__", value, value_type, [value_1], [value_type_1])
        self.push(new_value_type, new_value)

    def visit_binary_subtract(self, instr):
        value_type, value = self.pop()
        value_type_1, value_1 = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__subtract__", value, value_type, [value_1], [value_type_1])
        self.push(new_value_type, new_value)

    def visit_binary_subscr(self, instr):
        value_type, value = self.pop()
        value_type_1, value_1 = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__get_item__", value, value_type, [value_1], [value_type_1])
        self.push(new_value_type, new_value)

    def visit_binary_lshift(self, instr):
        value_type, value = self.pop()
        value_type_1, value_1 = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__lshift__", value, value_type, [value_1],
                                                    [value_type_1])
        self.push(new_value_type, new_value)

    def visit_binary_rshift(self, instr):
        value_type, value = self.pop()
        value_type_1, value_1 = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__rshift__", value, value_type, [value_1],
                                                    [value_type_1])
        self.push(new_value_type, new_value)

    def visit_binary_and(self, instr):
        value_type, value = self.pop()
        value_type_1, value_1 = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__and__", value, value_type, [value_1],
                                                    [value_type_1])
        self.push(new_value_type, new_value)

    def visit_binary_xor(self, instr):
        value_type, value = self.pop()
        value_type_1, value_1 = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__xor__", value, value_type, [value_1],
                                                    [value_type_1])
        self.push(new_value_type, new_value)

    def visit_binary_or(self, instr):
        value_type, value = self.pop()
        value_type_1, value_1 = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__or__", value, value_type, [value_1],
                                                    [value_type_1])
        self.push(new_value_type, new_value)

    """
    Compare
    """

    def visit_compare_op(self, instr):
        value_type, value = self.pop()
        value_type_1, value_1 = self.pop()
        new_value = caller.call_callable(self, value, [value_1], {})
        self.push(None, new_value)

    """
    Call
    """

    def visit_call_function(self, instr):
        args_count = instr.arg
        args = []
        arg_types = []
        for i in range(args_count):
            new_arg_type, new_arg = self.pop()
            args.insert(0, new_arg)
            arg_types.insert(0, arg_types)
        callable_type, callable = self.pop()
        caller.call_obj(self, )

    """
    Block stack
    """

    def visit_pop_block(self, instr):
        self.pop_block()

    def visit_pop_except(self, instr):
        raise NotImplementedError()
        self.pop_block()

    def visit_load_const(self, instr):
        self.push(None, self.__consts[instr.arg])

    def visit_load_attr(self, instr):
        str_value = self.__consts[instr.arg]
        value_type, value = self.pop()
        fly_obj.py_obj_get_attr(self, value, str_value, None)

    def visit_make_function(self, instr):
        pass

    def visit_store_name(self, instr):
        name = self.__code_obj.co_names[instr.arg]
        str_value = self.__code_gen.get_or_insert_str(name)
        self.__name = self.__builder.global_var(str_value)

    def visit_store_attr(self, instr):
        name = self.__code_obj.co_names[instr.namei]
        str_value = self.__code_gen.get_or_insert_str(name)
        self.__name = self.__builder.global_var(str_value)
        value_type, value = self.pop()
        fly_obj.py_obj_set_attr(self, value, str_value, self.__name, None)

    """
    Data structure
    """

    def visit_build_tuple(self, instr):
        element_counts = instr.arg
        import flyable.code_gen.tuple as gen_tuple
        new_tuple = gen_tuple.python_tuple_new(self.__code_gen, self.__builder,
                                               self.__builder.const_int64(element_counts))
        for i in range(element_counts):
            e_type, e_value = self.pop()
            gen_tuple.python_tuple_set_unsafe(self, new_tuple, i, e_value)
        self.push(None, new_tuple)

    def visit_build_list(self, instr):
        element_counts = instr.arg
        import flyable.code_gen.list as gen_list
        new_list = gen_list.instanciate_python_list(self.__code_gen, self.__builder,
                                                    self.__builder.const_int64(element_counts))
        element_counts = instr.arg
        for i in range(element_counts):
            e_type, e_value = self.pop()
            obj_ptr = gen_list.python_list_array_get_item_ptr_unsafe(self, new_list, i, e_value)
            self.__builder.sotre(e_value, obj_ptr)
        self.push(None, new_list)

    def visit_list_extend(self, instr):
        pass

    def visit_build_set(self, instr):
        raise NotImplementedError()

    """
    Attr
    """

    def visit_load_attr(self, instr):
        name = self.__code_obj.co_names[instr.namei]
        str_value = self.__code_gen.get_or_insert_str(name)
        self.__name = self.__builder.global_var(str_value)
        value_type, value = self.pop()
        new_attr = fly_obj.py_obj_get_attr(self, value, self.__name, None)
        self.push(None, new_attr)

    """
    JUMP
    """

    def visit_pop_jump_if_true(self, instr):
        instr_to_jump = self.__instructions[instr.arg]
        block_to_jump = self.__jumps_instr[instr_to_jump]
        else_block = self.__builder.create_block()
        value_type, value = self.pop()
        cond_value = _cond.value_to_cond(self, lang_type.get_python_obj_type(), value)
        self.__builder.cond_br(cond_value[1], block_to_jump, else_block)
        self.__builder.set_insert_block(else_block)

    def visit_pop_jump_if_false(self, instr):
        instr_to_jump = self.__instructions[instr.arg]
        block_to_jump = self.__jumps_instr[instr_to_jump]
        else_block = self.__builder.create_block()
        value_type, value = self.pop()
        cond_value = _cond.value_to_cond(self, lang_type.get_python_obj_type(), value)
        self.__builder.cond_br(cond_value[1], else_block, block_to_jump)
        self.__builder.set_insert_block(else_block)

    def visit_jump_if_not_exc_match(self, instr):
        pass

    def visit_jump_if_true_or_pop(self, instr):
        pass

    def visit_jump_if_false_or_pop(self, instr):
        pass

    def visit_jump_absolute(self, instr):
        pass

    def visit_jump_for_iter(self, instr):
        value_type, value = self.pop()
        value_type_1, value_1 = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__next__", value, value_type, [value_1], [value_type_1])

    def visit_load_global(self, instr):
        pass

    def visit_setup_finally(self, instr):
        pass

    def visit_load_fast(self, instr):
        var_name = self.__code_obj.co_varnames[instr.arg]
        found_var = self.get_or_gen_var(var_name)
        self.push(lang_type.get_python_obj_type(), self.__builder.load(found_var.get_code_value()))

    def visit_store_fast(self, instr):
        var_name = self.__code_obj.co_varnames[instr.arg]
        store_type, store_value = self.pop()
        found_var = self.get_or_gen_var(var_name)
        self.__builder.store(store_value, found_var.get_code_value())

    def visit_delete_fast(self, instr):
        var_name = self.__code_obj.co_varnames[instr.arg]
        found_var = self.get_or_gen_var(var_name)
        null_value = self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))
        self.__builder.store(null_value, found_var.get_code_value())

    def visit_return_value(self, instr):
        value_type, value = self.pop()
        self.__builder.ret(value)

    def push(self, type, value):
        if type is None:
            type = lang_type.get_python_obj_type()

        if not isinstance(value, int):
            raise TypeError("Value expected to be a int instead of " + str(value))

        self.__stack.append((type, value))

    def pop(self):
        value_pop = self.__stack.pop(-1)
        return value_pop

    def push_block(self, block):
        self.__blocks_stack.append(block)

    def pop_block(self):
        return self.__blocks_stack.pop(-1)

    def __get_code_func(self):
        code_func = self.__func.get_code_func()
        return code_func

    def get_code_gen(self):
        return self.__code_gen

    def get_builder(self):
        return self.__builder

    def generate_entry_block_var(self, alloca_type):
        current_block = self.__builder.get_current_block()
        self.__builder.set_insert_block(self.__entry_block)
        new_alloca = self.__builder.alloca(alloca_type)
        self.__builder.set_insert_block(current_block)
        return new_alloca

    def get_or_gen_var(self, var_name):
        found_var = self.__context.get_var(var_name)
        if found_var is None:
            import flyable.data.variable as _var
            found_var = _var.Variable(var_name)
            self.__context.add_var(found_var, lang_type.get_python_obj_type())
            found_var.set_code_value(self.generate_entry_block_var(code_type.get_py_obj_ptr(self.__code_gen)))
        return found_var

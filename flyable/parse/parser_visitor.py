import sys

import flyable.code_gen.code_gen as gen

import flyable.data.comp_data as comp_data
import dis as dis
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as _gen
import flyable.code_gen.runtime as runtime
import flyable.code_gen.caller as caller
import flyable.code_gen.fly_obj as fly_obj
import flyable.code_gen.cond as _cond
import flyable.code_gen.ref_counter as ref_counter
import flyable.data.lang_type as lang_type
import flyable.data.lang_func_impl as func_impl
import flyable.code_gen.set as gen_set
import flyable.code_gen.function as func
import flyable.code_gen.unpack as unpack
import flyable.code_gen.op_call as op_call
import flyable.code_gen.list as gen_list
import flyable.code_gen.dict as gen_dict
import flyable.code_gen.tuple as gen_tuple
import flyable.parse.version as version
import flyable.code_gen.function as function
import flyable.code_gen.iterator as gen_iter
import flyable.code_gen.exception as excp

import flyable.parse.exception.unsupported as unsupported


class DuckParserVisitor:

    def __init__(self, codegen, builder):
        self.__builder = builder
        self.__code_gen = codegen

    def get_builder(self):
        return self.__builder

    def get_code_gen(self):
        return self.__code_gen


class ParserVisitor:

    def __init__(self, parser, code_gen, func_impl):
        self.__code_gen: gen.CodeGen = code_gen
        self.__func = func_impl
        self.__parser = parser
        self.__data: comp_data.CompData = parser.get_data()
        self.__code_obj = None
        self.__bytecode = None
        self.__context = func_impl.get_context()

        self.__frame_ptr_value = None

        self.__kw_names = {}
        self.__jumps_instr = {}
        self.__instructions = []
        self.__current_instr_index = - 1
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
        if sys.version_info.major == 3 and sys.version_info.minor >= 11:
            self.__bytecode = dis.Bytecode(self.__bytecode.codeobj.co_consts[0])
        else:
            self.__bytecode = dis.Bytecode(self.__bytecode.codeobj.co_consts[0])
        self.__code_obj = self.__bytecode.codeobj
        self.__frame_ptr_value = 0

        self.__build_const()

        for instr in self.__bytecode:
            self.__instructions.append(instr)
            if instr.is_jump_target:
                new_block = self.__builder.create_block("Instr:" + instr.opname)
                self.__jumps_instr[instr] = new_block
        print("---")
        self.__setup_argument()

        for i, instr in enumerate(self.__instructions):
            self.__current_instr_index = i
            print(instr.opname + " " + str(self.__get_diamond_instr_jump(instr)) + " ")
            self.__visit_instr(instr)

        self.__builder.set_insert_block(self.__entry_block)
        self.__builder.br(self.__content_block)

        self.__code_gen.fill_not_terminated_block(self)

    def __setup_argument(self):
        callable_value = 0
        args_value = 1
        kwargs = 2
        if self.__func.get_impl_type() == func_impl.FuncImplType.TP_CALL:
            for i, arg in enumerate(self.__func.get_parent_func().get_node().args.args):
                arg_var = self.get_or_gen_var(arg.arg)
                index = self.__builder.const_int64(i)
                item_ptr = gen_tuple.python_tuple_get_unsafe_item_ptr(self, lang_type.get_python_obj_type(), 1, index)
                arg_var.set_code_value(item_ptr)
        elif self.__func.get_impl_type() == func_impl.FuncImplType.VEC_CALL:
            for i, arg in enumerate(self.__func.get_parent_func().get_node().args.args):
                arg_var = self.get_or_gen_var(arg.arg)
                item_ptr = self.__builder.gep2(args_value, code_type.get_py_obj_ptr(self.__code_gen),
                                               [self.__builder.const_int64(i)])
                arg_var.set_code_value(item_ptr)

    def __visit_instr(self, instr):

        if instr in self.__jumps_instr:
            insert_block = self.__jumps_instr[instr]
            # If we're not already the on the block
            if self.__builder.get_current_block() != insert_block:
                self.__builder.br(insert_block)
                self.__builder.set_insert_block(insert_block)

            diamond_jump = self.__get_diamond_instr_jump(instr)
            if diamond_jump >= 2 and self.stack_size() >= 2:  # The two top values need to be replaced by an alloca load
                values = []
                for i in range(diamond_jump):
                    values.append(self.pop()[1])
                preds = self.__func.get_code_func().get_pred_block(self.__builder.get_current_block())
                phi_value = self.__builder.phi(code_type.get_py_obj_ptr(self.__code_gen), values, preds)
                self.push(None, phi_value)

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
            self.__consts.append(self.__gen_const_value(const_obj))

    def __gen_const_value(self, const_obj):
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
            new_const = runtime.value_to_pyobj(self, const_value, lang_type.get_int_type())
            new_const = new_const[1]
        elif isinstance(const_obj, tuple):
            global_tuple = self.__code_gen.get_or_insert_const(const_obj)
            new_const = self.__builder.global_var(global_tuple)
            new_const = self.__builder.load(new_const)
        elif isinstance(const_obj, frozenset):
            global_set = self.__code_gen.get_or_insert_const(const_obj)
            new_const = self.__builder.global_var(global_set)
            new_const = self.__builder.load(new_const)
        elif type(const_obj).__name__ == "code":
            new_const = None
        else:
            raise Exception(
                "Not supported const of type " + str(type(const_obj)) + "with content " + str(const_obj))
        return new_const

    """"
    General instructions
    """

    def visit_nop(self, instr):
        pass

    def visit_resume(self, instr):
        pass

    def visit_cache(self, instr):
        pass

    def visit_pop_top(self, instr):
        type, value = self.pop()
        ref_counter.ref_decr(self, type, value)

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

    def visit_rot_n(self, instr):
        buffer = self.__stack[-1]
        for i in range(instr.arg):
            if i + 1 == instr.arg:
                self.__stack[-instr.arg] = buffer
            else:
                self.__stack[-i - 1] = self.__stack[-i - 2]

    def visit_dup_top(self, instr):
        type, value = self.__stack[-1]
        self.push(type, value)
        ref_counter.ref_incr(self.__builder, type, value)

    def visit_dup_top_two(self, instr):
        type, value = self.__stack[-2]
        self.push(type, value)
        ref_counter.ref_incr(self.__builder, type, value)
        type, value = self.__stack[-2]
        self.push(type, value)
        ref_counter.ref_incr(self.__builder, type, value)

    def visit_copy(self, instr):
        index = instr.arg
        type, value = self.__stack[-index]
        self.push(type, value)
        ref_counter.ref_incr(self.__builder, type, value)

    def visit_swap(self, instr):
        index = (-instr.arg)
        buffer = self.__stack[-1]
        self.__stack[-1] = self.__stack[index]
        self.__stack[index] = buffer

    def visit_push_null(self, instr):
        self.push(None, self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen)))

    """"
    Unary operations
    """

    def visit_unary_positive(self, instr):
        value_type, value = self.pop()
        op_func = self.__code_gen.get_or_create_func("PyNumber_Positive",
                                                     code_type.get_py_obj_ptr(self.__code_gen),
                                                     [code_type.get_py_obj_ptr(self.__code_gen)],
                                                     _gen.Linkage.EXTERNAL)
        new_value = self.__builder.call(op_func, [value])
        new_value_type = lang_type.get_python_obj_type()
        ref_counter.ref_decr(self, value_type, value)
        self.push(new_value_type, new_value)

    def visit_unary_negative(self, instr):
        value_type, value = self.pop()
        op_func = self.__code_gen.get_or_create_func("PyNumber_Negative",
                                                     code_type.get_py_obj_ptr(self.__code_gen),
                                                     [code_type.get_py_obj_ptr(self.__code_gen)],
                                                     _gen.Linkage.EXTERNAL)
        new_value = self.__builder.call(op_func, [value])
        new_value_type = lang_type.get_python_obj_type()
        ref_counter.ref_decr(self, value_type, value)
        self.push(new_value_type, new_value)

    def visit_unary_not(self, instr):
        value_type, value = self.pop()
        new_value_type, new_value = caller.call_obj(self, "__not__", value, value_type, [], [])
        ref_counter.ref_decr(self, value_type, value)
        self.push(new_value_type, new_value)

    def visit_unary_invert(self, instr):
        value_type, value = self.pop()
        op_func = self.__code_gen.get_or_create_func("PyNumber_Invert",
                                                     code_type.get_py_obj_ptr(self.__code_gen),
                                                     [code_type.get_py_obj_ptr(self.__code_gen)],
                                                     _gen.Linkage.EXTERNAL)
        new_value = self.__builder.call(op_func, [value])
        new_value_type = lang_type.get_python_obj_type()
        ref_counter.ref_decr(self, value_type, value)
        self.push(new_value_type, new_value)

    def visit_get_iter(self, instr):
        value_type, value = self.pop()

        get_iter_func = self.__code_gen.get_or_create_func("PyObject_GetIter",
                                                           code_type.get_py_obj_ptr(self.__code_gen),
                                                           [code_type.get_py_obj_ptr(self.__code_gen)],
                                                           _gen.Linkage.EXTERNAL)
        iter_value = self.__builder.call(get_iter_func, [value])

        ref_counter.ref_decr(self, value_type, value)

        self.push(None, iter_value)

    def visit_get_yield_from_iter(self, instr):
        raise unsupported.FlyableUnsupported()

    """"
    Binary operations
    """

    def visit_binary_op(self, instr):
        op_type = instr.arg
        op = op_call.get_binary_op_func_to_call(op_type)
        self.binary_or_inplace_visit(op)

    def visit_binary_power(self, instr):
        self.binary_or_inplace_visit("_PyNumber_PowerNoMod")

    def visit_binary_multiply(self, instr):
        self.binary_or_inplace_visit("PyNumber_Multiply")

    def visit_binary_matrix_multiply(self, instr):
        self.binary_or_inplace_visit("PyNumber_MatrixMultiply")

    def visit_binary_floor_divide(self, instr):
        self.binary_or_inplace_visit("PyNumber_FloorDivide")

    def visit_binary_true_divide(self, instr):
        self.binary_or_inplace_visit("PyNumber_TrueDivide")

    def visit_binary_modulo(self, instr):
        self.binary_or_inplace_visit("PyNumber_Remainder")
        # TODO: we should check if it's a string formatting and call PyUnicode_Format

    def visit_binary_add(self, instr):
        self.binary_or_inplace_visit("PyNumber_Add")
        # TODO: we should check if it's a concatenation

    def visit_binary_subtract(self, instr):
        self.binary_or_inplace_visit("PyNumber_Subtract")

    def visit_binary_subscr(self, instr):
        sub_type, sub_value = self.pop()
        container_type, container_value = self.pop()
        get_item_func = self.__code_gen.get_or_create_func("PyObject_GetItem",
                                                           code_type.get_py_obj_ptr(self.__code_gen),
                                                           [code_type.get_py_obj_ptr(self.__code_gen)] * 2,
                                                           _gen.Linkage.EXTERNAL)
        get_value = self.__builder.call(get_item_func, [container_value, sub_value])
        ref_counter.ref_decr(self, container_type, container_value)
        ref_counter.ref_decr(self, sub_type, sub_value)
        self.push(None, get_value)

    def visit_binary_lshift(self, instr):
        self.binary_or_inplace_visit("PyNumber_Lshift")

    def visit_binary_rshift(self, instr):
        self.binary_or_inplace_visit("PyNumber_Rshift")

    def visit_binary_and(self, instr):
        self.binary_or_inplace_visit("PyNumber_And")

    def visit_binary_xor(self, instr):
        self.binary_or_inplace_visit("PyNumber_Xor")

    def visit_binary_or(self, instr):
        self.binary_or_inplace_visit("PyNumber_Or")

    """
    In-place operations
    """

    def visit_inplace_power(self, instr):
        self.binary_or_inplace_visit("_PyNumber_InPlacePowerNoMod")

    def visit_inplace_multiply(self, instr):
        self.binary_or_inplace_visit("PyNumber_InPlaceMultiply")

    def visit_inplace_matrix_multiply(self, instr):
        self.binary_or_inplace_visit("PyNumber_InPlaceMatrixMultiply")

    def visit_inplace_floor_divide(self, instr):
        self.binary_or_inplace_visit("PyNumber_InPlaceFloorDivide")

    def visit_inplace_true_divide(self, instr):
        self.binary_or_inplace_visit("PyNumber_InPlaceTrueDivide")

    def visit_inplace_modulo(self, instr):
        self.binary_or_inplace_visit("PyNumber_InPlaceRemainder")

    def visit_inplace_add(self, instr):
        self.binary_or_inplace_visit("PyNumber_InPlaceAdd")
        # TODO: we should check if it's a concatenation

    def visit_inplace_subtract(self, instr):
        self.binary_or_inplace_visit("PyNumber_InPlaceSubtract")

    def visit_inplace_subscr(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_inplace_lshift(self, instr):
        self.binary_or_inplace_visit("PyNumber_InPlaceLshift")

    def visit_inplace_rshift(self, instr):
        self.binary_or_inplace_visit("PyNumber_InPlaceRshift")

    def visit_inplace_and(self, instr):
        self.binary_or_inplace_visit("PyNumber_InPlaceAnd")

    def visit_inplace_xor(self, instr):
        self.binary_or_inplace_visit("PyNumber_InPlaceXor")

    def visit_inplace_or(self, instr):
        self.binary_or_inplace_visit("PyNumber_InPlaceOr")

    def visit_store_subscr(self, instr):
        sub_type, sub_value = self.pop()
        container_type, container_value = self.pop()
        value_type, value_value = self.pop()
        set_item_func = self.__code_gen.get_or_create_func("PyObject_SetItem",
                                                           code_type.get_int32(),
                                                           [code_type.get_py_obj_ptr(self.__code_gen)] * 3,
                                                           _gen.Linkage.EXTERNAL)
        self.__builder.call(set_item_func, [container_value, sub_value, value_value])
        ref_counter.ref_decr(self, value_type, value_value)
        ref_counter.ref_decr(self, container_type, container_value)
        ref_counter.ref_decr(self, sub_type, sub_value)

    def visit_delete_subscr(self, instr):
        sub_type, sub_value = self.pop()
        container_type, container_value = self.pop()
        get_item_func = self.__code_gen.get_or_create_func("PyObject_DelItem",
                                                           code_type.get_int32(),
                                                           [code_type.get_py_obj_ptr(self.__code_gen)] * 2,
                                                           _gen.Linkage.EXTERNAL)
        self.__builder.call(get_item_func, [container_value, sub_value])
        ref_counter.ref_decr(self, container_type, container_value)
        ref_counter.ref_decr(self, sub_type, sub_value)

    """
    Coroutine opcodes
    """

    def visit_get_awaitable(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_get_aiter(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_get_anext(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_end_async_for(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_before_async_with(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_setup_async_with(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_async_gen_wrap(self, instr):
        obj_type, obj_value = self.top()
        async_gen_value_wrapper_new_func = self.__code_gen.get_or_create_func(
            "_PyAsyncGenValueWrapperNew",
            code_type.get_py_obj_ptr(self.__code_gen),
            [code_type.get_py_obj_ptr(self.__code_gen)],
            _gen.Linkage.EXTERNAL
        )
        new_value = self.__builder.call(
            async_gen_value_wrapper_new_func,
            [obj_value]
        )
        self.set_top(None, new_value)
        ref_counter.ref_decr(self, obj_type, obj_value)
        # TODO Dispatch()?

    """
    Compare
    """

    def visit_compare_op(self, instr):
        right_type, right_value = self.pop()
        left_type, left_value = self.pop()

        compare_func = self.__code_gen.get_or_create_func("PyObject_RichCompare",
                                                          code_type.get_py_obj_ptr(self.__code_gen),
                                                          [code_type.get_py_obj_ptr(self.__code_gen),
                                                           code_type.get_py_obj_ptr(self.__code_gen),
                                                           code_type.get_int32()],
                                                          _gen.Linkage.EXTERNAL)

        compare_value = self.__builder.call(compare_func,
                                            [left_value, right_value, self.__builder.const_int32(instr.arg)])

        self.push(None, compare_value)
        ref_counter.ref_decr(self, left_type, left_value)
        ref_counter.ref_decr(self, right_type, right_value)

    def visit_is_op(self, instr):
        right_type, right_value = self.pop()
        left_type, left_value = self.pop()

        result_val = self.__builder.eq(fly_obj.get_py_obj_type_ptr(self.__builder, left_value),
                                       fly_obj.get_py_obj_type_ptr(self.__builder, right_value))

        if instr.arg:
            self.__builder.neg(result_val)

        result_type, result_value = runtime.value_to_pyobj(self, result_val, lang_type.get_bool_type())
        ref_counter.ref_incr(self.__builder, result_type, result_value)
        self.push(result_type, result_value)

        ref_counter.ref_decr(self, left_type, left_value)
        ref_counter.ref_decr(self, right_type, right_value)

    def visit_contains_op(self, instr):
        right_type, right_value = self.pop()
        left_type, left_value = self.pop()

        """
        CPython has a special case for __contains__ where the left and right args are reversed
        ex: "a" in "abc" --> "abc".__contains__("a")
        """

        contains_func = self.__code_gen.get_or_create_func("PySequence_Contains", code_type.get_int32(),
                                                           [code_type.get_py_obj_ptr(self.__code_gen)] * 2,
                                                           _gen.Linkage.EXTERNAL)
        result_val = self.__builder.call(contains_func, [right_value, left_value])
        one = self.__builder.const_int32(1)

        if instr.arg:
            result_val = self.__builder.ne(result_val, one)
        else:
            result_val = self.__builder.eq(result_val, one)

        result_type, result_val = runtime.value_to_pyobj(self, result_val, lang_type.get_bool_type())
        ref_counter.ref_incr(self.__builder, result_type, result_val)
        self.push(result_type, result_val)

        ref_counter.ref_decr(self, left_type, left_value)
        ref_counter.ref_decr(self, right_type, right_value)

    """
    Call
    """

    def visit_kw_names(self, instr):
        self.__kw_names = self.__code_obj.co_consts[instr.arg]

    def visit_precall(self, instr):
        pass

    def visit_call(self, instr):

        args_count = instr.arg

        result_value = self.generate_entry_block_var(code_type.get_py_obj_ptr(self.__code_gen))

        arg_types = []
        arg_values = []
        for i in range(args_count):
            new_type, new_value = self.pop()
            arg_types.append(new_type)
            arg_values.append(new_value)

        arg_types.reverse()
        arg_values.reverse()

        first_type, first_value = self.pop()  # Callable or self
        second_type, second_value = self.pop()  # NULL or method

        is_method_block = self.__builder.create_block()
        not_method_block = self.__builder.create_block()
        continue_block = self.__builder.create_block()

        is_meth = self.__builder.ne(second_value, self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen)))
        self.__builder.cond_br(is_meth, is_method_block, not_method_block)

        self.__builder.set_insert_block(is_method_block)
        ref_counter.ref_incr(self.__builder, first_type, first_value)
        ref_counter.ref_incr(self.__builder, second_type, second_value)
        value = caller.call_callable(self, first_value, second_value, [first_value] + arg_values, self.__kw_names)
        self.__builder.store(value, result_value)
        self.__builder.br(continue_block)

        self.__builder.set_insert_block(not_method_block)
        ref_counter.ref_incr(self.__builder, first_type, first_value)
        value = caller.call_callable(self, first_value, first_value, arg_values, self.__kw_names)
        self.__builder.store(value, result_value)
        self.__builder.br(continue_block)

        self.__builder.set_insert_block(continue_block)

        self.push(None, self.__builder.load(result_value))
        self.__kw_names = {}

        for i, arg_value in enumerate(arg_values):
            ref_counter.ref_decr(self, arg_types[i], arg_value)

    def visit_call_function(self, instr):
        args_count = instr.arg

        arg_types = []
        arg_values = []
        for i in range(args_count):
            new_type, new_value = self.pop()
            arg_types.append(new_type)
            arg_values.append(new_value)

        arg_types.reverse()
        arg_values.reverse()

        callable_type, callable_value = self.pop()

        call_result_value = caller.call_callable(self, callable_value, callable_value, arg_values, self.__kw_names)
        self.push(None, call_result_value)
        self.__kw_names = {}

        for i, arg_value in enumerate(arg_values):
            ref_counter.ref_decr(self, arg_types[i], arg_value)

    def visit_call_function_ex(self):
        raise unsupported.FlyableUnsupported()

    def visit_call_function_kw(self, instr):
        args_count = instr.a
        tuple_type, tuple_args = self.pop()
        args = []
        arg_types = []
        for i in range(args_count):
            new_arg_type, new_arg = self.pop()
            args.insert(0, new_arg)
            arg_types.insert(0, arg_types)
        call_result_type, call_result_value = caller.call_callable(self, callable, args, {})
        for i, arg in enumerate(args):
            ref_counter.ref_decr(self, arg_types[i], arg)
        ref_counter.ref_decr(self, tuple_type, tuple_args)

    def visit_load_method(self, instr):
        found_attr = self.generate_entry_block_var(code_type.get_py_obj_ptr(self.__code_gen))
        str_value = self.__code_obj.co_names[instr.arg]
        str_var = self.__code_gen.get_or_insert_str(str_value)
        str_var = self.__builder.load(self.__builder.global_var(str_var))

        value_type, value = self.pop()

        get_method_func = self.__code_gen.get_or_create_func("_PyObject_GetMethod",
                                                             code_type.get_int32(),
                                                             ([code_type.get_py_obj_ptr(self.__code_gen)] * 2) +
                                                             [code_type.get_py_obj_ptr(self.__code_gen).get_ptr_to()],
                                                             _gen.Linkage.EXTERNAL)

        is_method = self.__builder.call(get_method_func, [value, str_var, found_attr])

        first_push_alloca = self.generate_entry_block_var(code_type.get_py_obj_ptr(self.__code_gen))
        second_push_alloca = self.generate_entry_block_var(code_type.get_py_obj_ptr(self.__code_gen))

        is_method_block = self.__builder.create_block()
        not_method_block = self.__builder.create_block()
        continue_block = self.__builder.create_block()

        is_method = self.__builder.ne(is_method, self.__builder.const_int32(0))
        self.__builder.cond_br(is_method, is_method_block, not_method_block)

        self.__builder.set_insert_block(is_method_block)
        self.__builder.store(self.__builder.load(found_attr), first_push_alloca)
        self.__builder.store(value, second_push_alloca)
        self.__builder.br(continue_block)

        self.__builder.set_insert_block(not_method_block)
        self.__builder.store(self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen)), first_push_alloca)
        self.__builder.store(self.__builder.load(found_attr), second_push_alloca)
        self.__builder.br(continue_block)

        self.__builder.set_insert_block(continue_block)

        self.push(None, self.__builder.load(first_push_alloca))
        self.push(value_type, self.__builder.load(second_push_alloca))

    def visit_call_method(self, instr):

        args_count = instr.arg

        result_value = self.generate_entry_block_var(code_type.get_py_obj_ptr(self.__code_gen))

        arg_types = []
        arg_values = []
        for i in range(args_count):
            new_type, new_value = self.pop()
            arg_types.append(new_type)
            arg_values.append(new_value)

        arg_types.reverse()
        arg_values.reverse()

        first_type, first_value = self.pop()  # Callable or self
        second_type, second_value = self.pop()  # NULL or method

        is_method_block = self.__builder.create_block()
        not_method_block = self.__builder.create_block()
        continue_block = self.__builder.create_block()

        is_meth = self.__builder.ne(second_value, self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen)))
        self.__builder.cond_br(is_meth, is_method_block, not_method_block)

        self.__builder.set_insert_block(is_method_block)
        value = caller.call_callable(self, first_value, second_value, [first_value] + arg_values, {})
        self.__builder.store(value, result_value)
        self.__builder.br(continue_block)

        self.__builder.set_insert_block(not_method_block)
        value = caller.call_callable(self, first_value, first_value, arg_values, {})
        self.__builder.store(value, result_value)
        self.__builder.br(continue_block)

        self.__builder.set_insert_block(continue_block)

        self.push(None, self.__builder.load(result_value))

        for i, arg_value in enumerate(arg_values):
            ref_counter.ref_decr(self, arg_types[i], arg_value)

    def visit_make_function(self, instr):
        raise unsupported.FlyableUnsupported()

    """
    Block stack
    """

    def visit_pop_block(self, instr):
        self.pop_block()

    def visit_pop_except(self, instr):
        self.pop()

    def visit_load_const(self, instr):
        const_value = self.__consts[instr.arg]
        ref_counter.ref_incr(self.__builder, lang_type.get_python_obj_type(), const_value)
        self.push(None, const_value)

    def visit_load_name(self, instr):
        name = self.__code_obj.co_names[instr.arg]
        var = self.get_or_gen_var(name)
        self.push(None, self.__builder.load(var.get_code_value()))

    def visit_store_name(self, instr):
        name = self.__code_obj.co_names[instr.arg]
        var = self.get_or_gen_var(name)
        store_type, store_value = self.pop()
        self.__builder.store(store_value, var.get_code_value())

    def visit_delete_name(self, instr):
        name = self.__code_obj.co_names[instr.arg]
        str_value = self.__code_gen.get_or_insert_str(name)
        str_var = self.__builder.global_var(str_value)
        str_var = self.__builder.load(str_var)
        global_map = func.py_function_get_globals(self, 0)
        del_item_func = self.__code_gen.get_or_create_func("PyObject_DelItem", code_type.get_int32(),
                                                           [code_type.get_py_obj_ptr(self.__code_gen)] * 2,
                                                           _gen.Linkage.EXTERNAL)
        self.__builder.call(del_item_func, [global_map, str_var])

    def visit_store_attr(self, instr):
        name = self.__code_obj.co_names[instr.arg]
        owner_type, owner_value = self.pop()
        v_type, v_value = self.pop()
        fly_obj.py_obj_set_attr(self, owner_value, name, v_value, None)
        ref_counter.ref_decr(self, v_type, v_value)
        ref_counter.ref_decr(self, owner_type, owner_value)

    def visit_delete_attr(self, instr):
        name = self.__code_obj.co_names[instr.arg]
        owner_type, owner_value = self.pop()
        null_value = self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))
        fly_obj.py_obj_set_attr(self, owner_value, name, null_value)
        ref_counter.ref_decr(self, owner_type, owner_value)

    def visit_store_global(self, instr):
        str_name = self.__code_obj.co_names[instr.arg]
        str_var = self.__code_gen.get_or_insert_str(str_name)
        str_var = self.__builder.global_var(str_var)
        str_var = self.__builder.load(str_var)
        v_type, v_value = self.pop()
        val_type, val_value = runtime.value_to_pyobj(self, v_value, v_type)

        globals = function.py_function_get_globals(self, 0)
        gen_dict.python_dict_set_item(self, globals, str_var, val_value)
        ref_counter.ref_decr(self, v_type, v_value)

    def visit_delete_global(self, instr):
        str_name = self.__code_obj.co_names[instr.arg]
        str_var = self.__code_gen.get_or_insert_str(str_name)
        str_var = self.__builder.global_var(str_var)
        str_var = self.__builder.load(str_var)
        global_map = func.py_function_get_globals(self, 0)
        gen_dict.python_dict_del_item(self, global_map, str_var)

    def visit_setup_with(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_before_with(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_unpack_sequence(self, instr):
        seq_type, seq = self.pop()
        unpack.unpack_iterable(self, seq_type, seq, instr.arg, -1)
        ref_counter.ref_decr(self, seq_type, seq)

    def visit_unpack_sequence_adaptive(self, instr):
        raise unsupported.FlyableUnsupported

    def visit_unpack_sequence_two_tuple(self, instr):
        raise unsupported.FlyableUnsupported

    def visit_unpack_sequence_tuple(self, instr):
        seq_type, seq = self.__stack[-1]
        if not seq_type.is_tuple():
            self.visit_unpack_sequence(instr)
        unpack.unpack_list_or_tuple(self, seq_type, seq, instr)
        ref_counter.ref_decr(self, seq_type, seq)

    def visit_unpack_sequence_list(self, instr):
        seq_type, seq = self.__stack[-1]
        if not seq_type.is_list():
            self.visit_unpack_sequence(instr)
        unpack.unpack_list_or_tuple(self, seq_type, seq, instr)
        ref_counter.ref_decr(self, seq_type, seq)

    def visit_unpack_ex(self, instr):
        seq_type, seq = self.pop()
        nb_args_before_list = instr.arg & 0xFF
        nb_args_after_list = instr.arg >> 8
        unpack.unpack_iterable(self, seq_type, seq, nb_args_before_list, nb_args_after_list)
        ref_counter.ref_decr(self, seq_type, seq)

    """
    Data structure
    """

    def visit_build_tuple(self, instr):
        element_counts = instr.arg
        import flyable.code_gen.tuple as gen_tuple
        new_tuple = gen_tuple.python_tuple_new(self.__code_gen, self.__builder,
                                               self.__builder.const_int64(element_counts))
        for i in reversed(range(element_counts)):
            e_type, e_value = self.pop()
            index_value = self.__builder.const_int64(i)
            gen_tuple.python_tuple_set_unsafe(self, new_tuple, index_value, e_value)
        self.push(None, new_tuple)

    def visit_build_list(self, instr):
        element_counts = instr.arg
        import flyable.code_gen.list as gen_list
        new_list = gen_list.instanciate_python_list(self.__code_gen, self.__builder,
                                                    self.__builder.const_int64(element_counts))
        element_counts = instr.arg
        for i in reversed(range(element_counts)):
            e_type, e_value = self.pop()
            index_value = self.__builder.const_int64(i)
            obj_ptr = gen_list.python_list_array_get_item_ptr_unsafe(self, lang_type.get_python_obj_type(), new_list,
                                                                     index_value)
            self.__builder.store(e_value, obj_ptr)
        self.push(None, new_list)

    def visit_list_extend(self, instr):
        index = instr.arg
        iter_type, iter_value = self.pop()
        list_type, list_value = self.__stack[-index]
        extend_func = self.__code_gen.get_or_create_func("_PyList_Extend", code_type.get_py_obj_ptr(self.__code_gen),
                                                         [code_type.get_py_obj_ptr(self.__code_gen)] * 2,
                                                         _gen.Linkage.EXTERNAL)
        self.__builder.call(extend_func, [list_value, iter_value])
        ref_counter.ref_decr(self, iter_type, iter_value)

    def visit_list_to_tuple(self, instr):
        list_type, list_value = self.pop()
        list_as_tuple_func = self.__code_gen.get_or_create_func("PyList_AsTuple",
                                                                code_type.get_py_obj_ptr(self.__code_gen),
                                                                [code_type.get_py_obj_ptr(self.__code_gen)],
                                                                _gen.Linkage.EXTERNAL)
        new_tuple_value = self.__builder.call(list_as_tuple_func, [list_value])
        self.push(None, new_tuple_value)
        ref_counter.ref_decr(self, list_type, list_value)

    def visit_build_set(self, instr):
        counts = instr.arg
        iter_value = self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))
        # Iter is NULL in this case
        new_set = gen_set.instanciate_python_set(self, iter_value)

        for i in range(counts):
            element_type, element_value = self.pop()
            py_element_type, py_element_value = runtime.value_to_pyobj(self, element_value, element_type)
            gen_set.python_set_add(self, new_set, py_element_value)
            ref_counter.ref_decr(self, element_type, element_value)
        self.push(lang_type.get_set_of_python_obj_type(), new_set)

    def visit_set_update(self, instr):
        index = instr.arg
        iter_type, iter_value = self.pop()
        list_type, list_value = self.__stack[-index]
        extend_func = self.__code_gen.get_or_create_func("_PySet_Update", code_type.get_py_obj_ptr(self.__code_gen),
                                                         [code_type.get_py_obj_ptr(self.__code_gen)] * 2,
                                                         _gen.Linkage.EXTERNAL)
        self.__builder.call(extend_func, [list_value, iter_value])
        ref_counter.ref_decr(self, iter_type, iter_value)

    def visit_build_map(self, instr):
        import flyable.code_gen.dict as gen_dict
        new_dict = gen_dict.python_dict_new(self)
        keys = []
        values = []
        for i in range(instr.arg):
            values.append((self.pop()))
            keys.append((self.pop()))
        for i in reversed(range(instr.arg)):
            key_type, key_value = keys[i]
            value_type, value_value = values[i]
            py_key_type, py_key_value = runtime.value_to_pyobj(self, key_value, key_type)
            py_value_type, py_value_value = runtime.value_to_pyobj(self, value_value, value_type)

            gen_dict.python_dict_set_item(self, new_dict, py_key_value, py_value_value)
            ref_counter.ref_decr(self, key_type, key_value)
            ref_counter.ref_decr(self, value_type, value_value)

        self.push(lang_type.get_dict_of_python_obj_type(), new_dict)

    def visit_build_const_key_map(self, instr):
        import flyable.code_gen.dict as gen_dict
        import flyable.code_gen.tuple as gen_tuple
        new_dict = gen_dict.python_dict_new(self)
        keys_type, keys_value = self.pop()
        values = []
        for i in range(instr.arg):
            values.append((self.pop()))
        values.reverse()
        for i in range(instr.arg):
            value_type, value_value = values[i]
            py_value_type, py_value_value = runtime.value_to_pyobj(self, value_value, value_type)
            key_value = gen_tuple.python_tuple_get_unsafe_item_ptr(self, keys_type, keys_value,
                                                                   self.__builder.const_int64(i))
            key_value = self.__builder.load(key_value)
            gen_dict.python_dict_set_item(self, new_dict, key_value, py_value_value)
            ref_counter.ref_decr(self, value_type, value_value)

        ref_counter.ref_decr(self, keys_type, keys_value)
        self.push(lang_type.get_dict_of_python_obj_type(), new_dict)

    def visit_dict_update(self, instr):
        index = instr.arg
        update_type, update_value = self.pop()
        dict_type, dict_value = self.__stack[-index]
        update_func = self.__code_gen.get_or_create_func("PyDict_Update", code_type.get_py_obj_ptr(self.__code_gen),
                                                         [code_type.get_py_obj_ptr(self.__code_gen)] * 2,
                                                         _gen.Linkage.EXTERNAL)
        self.__builder.call(update_func, [dict_value, update_value])

    def visit_dict_merge(self, instr):
        update_type, update_value = self.pop()
        dict_type, dict_value = self.__stack[-instr.arg]
        two = self.__builder.const_int64(2)
        dict_merge_func = self.__code_gen.get_or_create_func("_PyDict_MergeEx",
                                                             code_type.get_py_obj_ptr(self.__code_gen),
                                                             [code_type.get_py_obj_ptr(self.__code_gen),
                                                              code_type.get_py_obj_ptr(self.__code_gen),
                                                              code_type.get_int32()],
                                                             _gen.Linkage.EXTERNAL)
        self.__builder.call(dict_merge_func, [dict_value, update_value, two])
        ref_counter.ref_decr(self, update_type, update_value)

    def visit_set_add(self, instr):
        item_type, item_value = self.pop()
        set_type, set_value = self.__stack[-instr.arg]
        gen_set.python_set_add(self, set_value, item_value)
        ref_counter.ref_decr(self, item_type, item_value)

    def visit_list_append(self, instr):
        item_type, item_value = self.pop()
        list_type, list_value = self.__stack[-instr.arg]
        gen_list.python_list_append(self, list_value, item_type, item_value)

    def visit_map_add(self, instr):
        value_type, value_value = self.pop()
        key_type, key_value = self.pop()
        dict_type, dict_value = self.__stack[-instr.arg]
        gen_dict.python_dict_set_item(self, dict_value, key_value, value_value)

    def visit_copy_dict_without_keys(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_get_len(self, instr):
        top_type, top_value = self.__stack[-1]
        if top_type.is_list():
            len = gen_list.python_list_len(self, top_value)
        elif top_type.is_tuple():
            len = gen_tuple.python_tuple_len(self, top_value)
        elif top_type.is_set():
            len = gen_set.python_set_len(self, top_value)
        elif top_type.is_dict():
            len = gen_dict.python_dict_len(self, top_value)
        else:
            len_func = self.__code_gen.get_or_create_func("PyObject_Length", code_type.get_int64(),
                                                          [code_type.get_py_obj_ptr(self.__code_gen)],
                                                          _gen.Linkage.EXTERNAL)
            len = self.__builder.call(len_func, [top_value])

        self.push(lang_type.get_int_type(), len)

    def visit_match_mapping(self, instr):
        py_tpflags_mapping = self.__builder.const_int64(64)
        subject_type, subject_value = self.__stack[-1]

        subject_type = fly_obj.get_py_obj_type(self.__builder, subject_value)
        tp_flag = function.py_obj_type_get_tp_flag_ptr(self, subject_type)
        tp_flag = self.__builder.load(tp_flag)

        match = self.__builder._and(tp_flag, py_tpflags_mapping)
        zero = self.__builder.const_int64(0)
        res = self.__builder.ne(match, zero)
        self.push(lang_type.get_bool_type(), res)
        ref_counter.ref_incr(self.__builder, lang_type.get_bool_type(), res)

    def visit_match_sequence(self, instr):
        py_tpflags_sequence = self.__builder.const_int64(32)
        subject_type, subject_value = self.__stack[-1]

        subject_type = fly_obj.get_py_obj_type(self.__builder, subject_value)
        tp_flag = function.py_obj_type_get_tp_flag_ptr(self, subject_type)
        tp_flag = self.__builder.load(tp_flag)

        match = self.__builder._and(tp_flag, py_tpflags_sequence)
        zero = self.__builder.const_int64(0)
        res = self.__builder.ne(match, zero)
        self.push(lang_type.get_bool_type(), res)
        ref_counter.ref_incr(self.__builder, lang_type.get_bool_type(), res)

    def visit_match_keys(self, instr):
        # TODO: do the visit with the runtime. Previously to 3.11 this instruction also pushed a boolean value
        #  indicating success (True) or failure (False).
        keys_type, keys_value = self.__stack[-1]
        subject_type, subject_value = self.__stack[-2]
        keys_size = gen_tuple.python_tuple_len(self, keys_value)
        new_tuple_value = gen_tuple.python_tuple_new(self.__code_gen, self.__builder, keys_size)
        new_tuple = self.generate_entry_block_var(code_type.get_tuple_obj_ptr(self.__code_gen))
        self.__builder.store(new_tuple_value, new_tuple)
        index_value = self.generate_entry_block_var(code_type.get_int64())
        self.__builder.store(self.__builder.const_int64(0), index_value)

        next_block = self.__builder.create_block("Next Block")
        check_index_block = self.__builder.create_block("Check Index Block")
        set_item_block = self.__builder.create_block("Set Item Block")
        null_block = self.__builder.create_block("Null Block")
        continue_block = self.__builder.create_block("Continue Block")
        self.__builder.br(check_index_block)

        self.__builder.set_insert_block(check_index_block)
        test = self.__builder.lt(index_value, keys_size)
        self.__builder.cond_br(test, next_block, continue_block)

        self.__builder.set_insert_block(next_block)
        args_types = [lang_type.get_int_type()]
        args = [index_value]
        item_type, item_value = caller.call_obj(self, "__getitem__", keys_value, keys_type, args, args_types, {})
        # TODO: we should check that item_value has no duplicates in keys
        dict_value = gen_dict.python_dict_get_item(self, subject_value, item_value)
        null_ptr = self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))
        test = self.__builder.eq(dict_value, null_ptr)
        self.__builder.cond_br(test, null_block, set_item_block)

        self.__builder.set_insert_block(set_item_block)
        gen_tuple.python_tuple_set_unsafe(self, new_tuple, index_value, dict_value)
        incr_index = self.__builder.add(index_value, self.__builder.const_int64(1))
        self.__builder.store(incr_index, index_value)
        self.__builder.br(check_index_block)

        self.__builder.set_insert_block(null_block)
        self.__builder.store(null_ptr, new_tuple)
        self.__builder.br(continue_block)

        self.__builder.set_insert_block(continue_block)
        self.push(lang_type.get_tuple_of_python_obj_type(), new_tuple)

    def visit_build_slice(self, instr):
        slices_count = instr.arg
        if slices_count == 3:
            step_type, step = self.pop()
        else:
            step_type, step = None, self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))
        stop_type, stop = self.pop()
        start_type, start = self.pop()
        new_slice_func = self.__code_gen.get_or_create_func("PySlice_New", code_type.get_py_obj_ptr(self.__code_gen),
                                                            [code_type.get_py_obj_ptr(self.__code_gen)] * 3,
                                                            _gen.Linkage.EXTERNAL)
        new_slice = self.__builder.call(new_slice_func, [start, stop, step])
        self.push(None, new_slice)
        ref_counter.ref_decr(self, start_type, start)
        ref_counter.ref_decr(self, stop_type, stop)
        ref_counter.ref_decr_nullable(self, step_type, step)

    """
    Attr
    """

    def visit_load_attr(self, instr):
        name = self.__code_obj.co_names[instr.arg]
        value_type, value = self.pop()
        new_attr = fly_obj.py_obj_get_attr(self, value, name, None)
        self.push(None, new_attr)
        ref_counter.ref_decr(self, value_type, value)

    """
    JUMP
    """

    def visit_jump_forward(self, instr):
        block_to_jump = self.get_block_to_jump_by(instr.offset, instr.arg)
        self.__builder.br(block_to_jump)

    def visit_jump_backward(self, instr):
        block_to_jump = self.get_block_to_jump_by(instr.offset, -instr.arg)
        self.__builder.br(block_to_jump)

    def visit_jump_backward_no_interrupt(self, instr):
        block_to_jump = self.get_block_to_jump_by(instr.offset, -instr.arg)
        self.__builder.br(block_to_jump)

    def visit_pop_jump_forward_if_true(self, instr):
        block_to_jump = self.get_block_to_jump_by(instr.offset, instr.arg)
        else_block = self.__get_else_instr_block()
        value_type, value = self.pop()
        cond_value = _cond.value_to_cond(self, lang_type.get_python_obj_type(), value)
        ref_counter.ref_decr(self, value_type, value)
        self.__builder.cond_br(cond_value[1], block_to_jump, else_block)
        self.__builder.set_insert_block(else_block)

    def visit_pop_jump_backward_if_true(self, instr):
        block_to_jump = self.get_block_to_jump_by(instr.offset, -instr.arg)
        else_block = self.__get_else_instr_block()
        value_type, value = self.pop()
        cond_value = _cond.value_to_cond(self, lang_type.get_python_obj_type(), value)
        ref_counter.ref_decr(self, value_type, value)
        self.__builder.cond_br(cond_value[1], block_to_jump, else_block)
        self.__builder.set_insert_block(else_block)

    def visit_pop_jump_forward_if_false(self, instr):
        block_to_jump = self.get_block_to_jump_by(instr.offset, instr.arg)
        else_block = self.__get_else_instr_block()
        value_type, value = self.pop()
        cond_value = _cond.value_to_cond(self, lang_type.get_python_obj_type(), value)
        ref_counter.ref_decr(self, value_type, value)
        self.__builder.cond_br(cond_value[1], else_block, block_to_jump)
        self.__builder.set_insert_block(else_block)

    def visit_pop_jump_backward_if_false(self, instr):
        block_to_jump = self.get_block_to_jump_by(instr.offset, -instr.arg)
        else_block = self.__get_else_instr_block()
        value_type, value = self.pop()
        cond_value = _cond.value_to_cond(self, lang_type.get_python_obj_type(), value)
        ref_counter.ref_decr(self, value_type, value)
        self.__builder.cond_br(cond_value[1], else_block, block_to_jump)
        self.__builder.set_insert_block(else_block)

    def visit_pop_jump_forward_if_not_none(self, instr):
        block_to_jump = self.get_block_to_jump_by(instr.offset, instr.arg)
        else_block = self.__get_else_instr_block()
        value_type, value = self.pop()
        none_value = self.__builder.global_var(self.__code_gen.get_none())
        cond_value = self.__builder.ne(none_value, value)
        ref_counter.ref_decr(self, value_type, value)
        self.__builder.cond_br(cond_value, block_to_jump, else_block)
        self.__builder.set_insert_block(else_block)

    def visit_pop_jump_backward_if_not_none(self, instr):
        block_to_jump = self.get_block_to_jump_by(instr.offset, -instr.arg)
        else_block = self.__get_else_instr_block()
        value_type, value = self.pop()
        none_value = self.__builder.global_var(self.__code_gen.get_none())
        cond_value = self.__builder.ne(none_value, value)
        ref_counter.ref_decr(self, value_type, value)
        self.__builder.cond_br(cond_value, block_to_jump, else_block)
        self.__builder.set_insert_block(else_block)

    def visit_pop_jump_forward_if_none(self, instr):
        block_to_jump = self.get_block_to_jump_by(instr.offset, instr.arg)
        else_block = self.__get_else_instr_block()
        value_type, value = self.pop()
        none_value = self.__builder.global_var(self.__code_gen.get_none())
        cond_value = self.__builder.eq(none_value, value)
        ref_counter.ref_decr(self, value_type, value)
        self.__builder.cond_br(cond_value, block_to_jump, else_block)
        self.__builder.set_insert_block(else_block)

    def visit_pop_jump_backward_if_none(self, instr):
        block_to_jump = self.get_block_to_jump_by(instr.offset, -instr.arg)
        else_block = self.__get_else_instr_block()
        value_type, value = self.pop()
        none_value = self.__builder.global_var(self.__code_gen.get_none())
        cond_value = self.__builder.eq(none_value, value)
        ref_counter.ref_decr(self, value_type, value)
        self.__builder.cond_br(cond_value, block_to_jump, else_block)
        self.__builder.set_insert_block(else_block)

    def visit_pop_jump_if_true(self, instr):
        block_to_jump = self.get_block_to_jump_to(instr.arg)
        else_block = self.__get_else_instr_block()
        value_type, value = self.pop()
        cond_value = _cond.value_to_cond(self, lang_type.get_python_obj_type(), value)
        ref_counter.ref_decr(self, value_type, value)
        self.__builder.cond_br(cond_value[1], block_to_jump, else_block)
        self.__builder.set_insert_block(else_block)

    def visit_pop_jump_if_false(self, instr):
        block_to_jump = self.get_block_to_jump_to(instr.arg)
        else_block = self.__get_else_instr_block()
        value_type, value = self.pop()
        cond_value = _cond.value_to_cond(self, lang_type.get_python_obj_type(), value)
        ref_counter.ref_decr(self, value_type, value)
        self.__builder.cond_br(cond_value[1], else_block, block_to_jump)
        self.__builder.set_insert_block(else_block)

    def visit_jump_if_not_exc_match(self, instr):
        self.push(None, self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen)))

    def visit_jump_if_true_or_pop(self, instr):
        self.visit_pop_jump_if_true(instr)

    def visit_jump_if_false_or_pop(self, instr):
        self.visit_pop_jump_if_false(instr)

    def visit_pop_jump_if_not_none(self, instr):
        block_to_jump = self.get_block_to_jump_to(instr.arg)
        else_block = self.__builder.create_block()
        value_type, value = self.pop()
        none_value = self.__builder.global_var(self.__code_gen.get_none())
        cond_value = self.__builder.ne(none_value, value)
        ref_counter.ref_decr(self, value_type, value)
        self.__builder.cond_br(cond_value, block_to_jump, else_block)
        self.__builder.set_insert_block(else_block)

    def visit_pop_jump_if_none(self, instr):
        block_to_jump = self.get_block_to_jump_to(instr.arg)
        else_block = self.__builder.create_block()
        value_type, value = self.pop()
        none_value = self.__builder.global_var(self.__code_gen.get_none())
        cond_value = self.__builder.eq(none_value, value)
        ref_counter.ref_decr(self, value_type, value)
        self.__builder.cond_br(cond_value, block_to_jump, else_block)
        self.__builder.set_insert_block(else_block)

    def visit_jump_absolute(self, instr):
        block_to_jump = self.get_block_to_jump_to(instr.arg)
        self.__builder.br(block_to_jump)

    def visit_for_iter(self, instr):
        iterable_type, iterator_value = self.top()

        next_value = gen_iter.call_iter_next_direct(self, iterator_value)
        self.push(None, next_value)

        null_ptr = self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))
        test = self.__builder.eq(next_value, null_ptr)
        continue_block = self.get_block_to_jump_by(instr.offset, instr.arg)
        next_block = self.__builder.create_block("Next Block")
        self.__builder.cond_br(test, continue_block, next_block)

        # clear the global excp when we leave the loop
        self.__builder.set_insert_block(continue_block)
        excp.py_runtime_clear_error(self.__code_gen, self.__builder)
        ref_counter.ref_decr(self, iterable_type, iterator_value)

        self.__builder.set_insert_block(next_block)

    def visit_load_global(self, instr):
        namei = instr.arg
        if version.get_python_version() >= version.PythonVersion.VERSION_3_11:
            if namei & 1:
                self.push(None, self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen)))
            namei = namei >> 1
        var_name = self.__code_obj.co_names[namei]

        str_name_value = self.__builder.global_var(self.__code_gen.get_or_insert_str(var_name))
        str_name_value = self.__builder.load(str_name_value)

        import builtins
        if hasattr(builtins, var_name):
            dict_value = func.py_function_get_builtins(self, self.__frame_ptr_value)
        else:
            dict_value = func.py_function_get_globals(self, self.__frame_ptr_value)
        global_value = func.py_dict_get_item(self, dict_value, str_name_value)
        self.push(None, global_value)

    def visit_setup_finally(self, instr):
        pass

    def visit_load_fast(self, instr):
        var_name = self.__code_obj.co_varnames[instr.arg]
        found_var = self.get_or_gen_var(var_name)
        value = self.__builder.load(found_var.get_code_value())
        ref_counter.ref_incr(self.__builder, lang_type.get_python_obj_type(), value)
        self.push(lang_type.get_python_obj_type(), value)

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

    def visit_load_closure(self, instr):
        var_name = self.__code_obj.co_varnames[instr.arg]
        found_var = self.get_or_gen_var(var_name)
        value = self.__builder.load(found_var.get_code_value())
        ref_counter.ref_incr(self.__builder, lang_type.get_python_obj_type(), value)
        self.push(lang_type.get_python_obj_type(), value)

    def visit_copy_free_vars(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_make_cell(self, instr):
        var_name = self.__code_obj.co_varnames[instr.arg]
        found_var = self.get_or_gen_var(var_name)
        initial = self.__builder.load(found_var.get_code_value())
        py_cell_get = self.__code_gen.get_or_create_func("PyCell_New",
                                                         code_type.get_py_obj_ptr(self.__code_gen),
                                                         [code_type.get_py_obj_ptr(self.__code_gen)],
                                                         _gen.Linkage.EXTERNAL)
        cell = self.__builder.call(py_cell_get, [initial])
        self.__builder.store(cell, found_var.get_code_value())

    def visit_load_deref(self, instr):
        var_name = self.__code_obj.co_varnames[instr.arg]
        found_var = self.get_or_gen_var(var_name)
        cell = self.__builder.load(found_var.get_code_value())
        py_cell_get = self.__code_gen.get_or_create_func("PyCell_GET",
                                                         code_type.get_py_obj_ptr(self.__code_gen),
                                                         [code_type.get_py_obj_ptr(self.__code_gen)],
                                                         _gen.Linkage.EXTERNAL)
        value = self.__builder.call(py_cell_get, [cell])
        ref_counter.ref_incr(self.__builder, lang_type.get_python_obj_type(), value)
        self.push(lang_type.get_python_obj_type(), value)

    def visit_load_classderef(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_store_deref(self, instr):
        v = self.pop()
        var_name = self.__code_obj.co_varnames[instr.arg]
        found_var = self.get_or_gen_var(var_name)
        cell = self.__builder.load(found_var.get_code_value())

        py_cell_get = self.__code_gen.get_or_create_func("PyCell_GET",
                                                         code_type.get_py_obj_ptr(self.__code_gen),
                                                         [code_type.get_py_obj_ptr(self.__code_gen)],
                                                         _gen.Linkage.EXTERNAL)
        oldobj = self.__builder.call(py_cell_get, [cell])

        py_cell_set = self.__code_gen.get_or_create_func("PyCell_SET",
                                                         code_type.get_py_obj_ptr(self.__code_gen),
                                                         [code_type.get_py_obj_ptr(self.__code_gen)] * 2,
                                                         _gen.Linkage.EXTERNAL)
        self.__builder.call(py_cell_set, [cell, v])

        ref_counter.ref_decr_nullable(self.__builder, lang_type.get_python_obj_type(), oldobj)

    def visit_delete_deref(self, instr):
        var_name = self.__code_obj.co_varnames[instr.arg]
        found_var = self.get_or_gen_var(var_name)
        cell = self.__builder.load(found_var.get_code_value())

        py_cell_get = self.__code_gen.get_or_create_func("PyCell_GET",
                                                         code_type.get_py_obj_ptr(self.__code_gen),
                                                         [code_type.get_py_obj_ptr(self.__code_gen)],
                                                         _gen.Linkage.EXTERNAL)
        oldobj = self.__builder.call(py_cell_get, [cell])

        null_value = self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen))
        py_cell_set = self.__code_gen.get_or_create_func("PyCell_SET",
                                                         code_type.get_py_obj_ptr(self.__code_gen),
                                                         [code_type.get_py_obj_ptr(self.__code_gen)] * 2,
                                                         _gen.Linkage.EXTERNAL)
        self.__builder.call(py_cell_set, [cell, null_value])

        ref_counter.ref_decr(self.__builder, lang_type.get_python_obj_type(), oldobj)

    def visit_return_value(self, instr):
        value_type, value = self.pop()
        self.__builder.ret(value)

    def visit_yield_value(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_yield_from(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_return_generator(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_send(self, instr):
        raise unsupported.FlyableUnsupported()

    """
    Miscellaneous opcodes
    """

    def visit_print_expr(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_setup_annotations(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_import_star(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_import_name(self, instr):
        raise unsupported.FlyableUnsupported()
        name = self.__code_obj.co_names[instr.arg]
        name_global_var = self.__code_gen.get_or_insert_str(name)
        name_str = self.__builder.global_var(name_global_var)
        name_str = self.__builder.load(name_str)
        from_type, from_value = self.pop()
        level_type, level_value = self.pop()

        import_call = self.__code_gen.get_or_create_func("flyable_import_name",
                                                         code_type.get_py_obj_ptr(self.__code_gen),
                                                         [code_type.get_py_obj_ptr(self.__code_gen)] * 3,
                                                         _gen.Linkage.EXTERNAL)

        import_value = self.__builder.call(import_call, [name_str, from_value, level_value])

        self.push(None, import_value)

    def visit_import_from(self, instr):
        raise unsupported.FlyableUnsupported()
        name_type, name_value = self.pop()
        from_type, from_value = self.pop()

    def visit_reraise(self, instr):
        lasti = instr.arg

        if lasti:
            self.__lasti = lasti

        # val_type, val_value = self.pop()

        new_re_func = self.__code_gen.get_or_create_func("Py_NewRef", code_type.get_py_obj_ptr(self.__code_gen),
                                                         [code_type.get_py_obj_ptr(self.__code_gen)] * 2,
                                                         _gen.Linkage.EXTERNAL)

    def visit_prep_reraise_star(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_raise_varargs(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_with_except_start(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_load_assertion_error(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_load_build_class(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_build_string(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_extended_arg(self, instr):
        # the disassembler takes care of this one
        pass

    def visit_format_value(self, instr):
        which_conversion = instr.arg & 0x3
        have_fmt_spec = (instr.arg & 0x4) == 0x4

        fmt_spec = self.pop()[1] if have_fmt_spec else self.__builder.const_null(
            code_type.get_py_obj_ptr(self.__code_gen))
        value_type, value_value = self.pop()

        match which_conversion:
            case 0x0:
                conv_fn = None
            case 0x1:
                conv_fn = "PyObject_Str"
            case 0x2:
                conv_fn = "PyObject_Repr"
            case 0x3:
                conv_fn = "PyObject_ASCII"
            case _:
                conv_fn = None
                self.__parser.throw_error("unexpected conversion flag " + str(which_conversion), None, None)

        if conv_fn != None:
            conv_func = self.__code_gen.get_or_create_func(conv_fn, code_type.get_py_obj_ptr(self.__code_gen),
                                                           [code_type.get_py_obj_ptr(self.__code_gen)],
                                                           _gen.Linkage.EXTERNAL)
            value_value = self.__builder.call(conv_func, [value_value])
        else:
            conv_func = self.__code_gen.get_or_create_func("PyObject_Format", code_type.get_py_obj_ptr(self.__code_gen),
                                                           [code_type.get_py_obj_ptr(self.__code_gen)] * 2,
                                                           _gen.Linkage.EXTERNAL)
            value_value = self.__builder.call(conv_func, [value_value, fmt_spec])

        self.push(value_type, value_value)
        ref_counter.ref_decr(self, value_type, value_value)
        ref_counter.ref_decr_nullable(self, lang_type.get_python_obj_type(), fmt_spec)

    def visit_match_class(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_gen_start(self, instr):
        raise unsupported.FlyableUnsupported()

    def visit_have_argument(self, instr):
        pass

    def visit_push_exc_info(self, instr):
        self.__blocks_stack.append(None)
        self.push(None, self.__builder.const_null(code_type.get_py_obj_ptr(self.__code_gen)))

    def visit_check_exc_match(self, instr):
        r_type, r_value = self.pop()
        right_type, right_value = runtime.value_to_pyobj(self, r_value, r_type)
        left_type, left_value = self.top()
        left_type, left_value = runtime.value_to_pyobj(self, left_value, left_type)

        excp_math_func = self.__code_gen.get_or_create_func("PyErr_GivenExceptionMatches", code_type.get_int32(),
                                                            [code_type.get_py_obj_ptr(self.__code_gen)] * 2,
                                                            _gen.Linkage.EXTERNAL)

        excp_match = self.__builder.call(excp_math_func, [left_value, right_value])
        excp_match = self.__builder.int_cast(excp_match, code_type.get_int64())
        match_type, match_value = runtime.value_to_pyobj(self, excp_match, lang_type.get_int_type())
        self.push(match_type, match_value)
        ref_counter.ref_decr(self, r_type, r_value)

    def visit_check_eg_match(self, instr):
        raise unsupported.FlyableUnsupported()

    """
    Visitor methods
    """

    def push(self, type, value):
        if type is None:
            type = lang_type.get_python_obj_type()

        if not isinstance(value, int):
            raise TypeError("Value expected to be a int instead of " + str(value))

        self.__stack.append((type, value))

    def pop(self):
        value_pop = self.__stack.pop(-1)
        return value_pop

    def set_top(self, new_type, new_value):
        self.__stack[-1] = (new_type, new_value)

    def top(self):
        return self.__stack[-1]

    def peek(self, index):
        return self.__stack[-index - 1]

    def stack_size(self):
        return len(self.__stack)

    def get_block_to_jump_to(self, x):
        offset_to_reach = x * 2
        for instr in self.__instructions:
            if instr.offset == offset_to_reach:
                block_to_reach = self.__jumps_instr[instr]
                return block_to_reach
        raise ValueError("Didn't find an instruction for the offset to reach " + str(x))

    def get_block_to_jump_by(self, current_offset, x):
        offset_to_reach = current_offset + x * 2 + 2  # We add 2 to get to the next instruction
        for instr in self.__instructions:
            if instr.offset == offset_to_reach:
                block_to_reach = self.__jumps_instr[instr]
                return block_to_reach
        raise ValueError("Didn't find an instruction for the offset to reach " + str(offset_to_reach))

    def push_block(self, block):
        self.__blocks_stack.append(block)

    def pop_block(self):
        return self.__blocks_stack.pop()

    def __get_code_func(self):
        code_func = self.__func.get_code_func()
        return code_func

    def __get_diamond_instr_jump(self, instr):
        """
        return if whether an instruction can be jumped from two different instructions. If that is the case, then
        it's a diamond instruction
        """
        count = 0
        if instr in self.__jumps_instr:  # Is it an instruction that we can jump into
            instr_block = self.__jumps_instr[instr]
            for i, e in enumerate(self.__instructions):
                if e is not instr:
                    opname = e.opname.lower()
                    if "jump" in opname and "forward" in opname:
                        if self.get_block_to_jump_by(e.offset, e.arg) is instr_block:
                            count += 1
                    elif "jump" in opname and "backward" in opname:
                        if self.get_block_to_jump_by(e.offset, -e.arg) is instr_block:
                            count += 1
                    elif "jump" in opname and e.arg * 2 == instr.offset:
                        if self.get_block_to_jump_to(e.arg) is instr_block:
                            count += 1

                    # Also check if it's the else block of a jump statement
                    if "jump" in opname and "if" in opname:  # Only conditional jumps have else statement
                        if i + 1 < len(self.__instructions):
                            else_instr = self.__instructions[i + 1]
                            # Else statement are not a jump target according to Python diss
                            if else_instr == instr:
                                count += 1
                else:  # Also check the case where a instr can be following a direct instr
                    if i > 0:
                        prec_instr = self.__instructions[i - 1]
                        if "jump" not in prec_instr.opname.lower():
                            count += 1
        return count

    def __get_else_instr_block(self):
        if self.__current_instr_index + 1 < len(self.__instructions):
            else_instr = self.__instructions[self.__current_instr_index + 1]
            if else_instr in self.__jumps_instr:
                return self.__jumps_instr[else_instr]
        else_block = self.__builder.create_block()
        self.__jumps_instr[else_instr] = else_block
        return else_block

    def get_func(self):
        return self.__func

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

    def get_or_gen_var(self, var_name: str | int):
        found_var = self.__context.get_var(var_name)
        if found_var is None:
            found_var = self.__context.add_var(var_name, lang_type.get_python_obj_type())
            found_var.set_code_value(self.generate_entry_block_var(code_type.get_py_obj_ptr(self.__code_gen)))
        return found_var

    def binary_or_inplace_visit(self, op_type: str):
        right_type, right_value = self.pop()
        left_type, left_value = self.pop()

        op_func = self.__code_gen.get_or_create_func(op_type,
                                                     code_type.get_py_obj_ptr(self.__code_gen),
                                                     [code_type.get_py_obj_ptr(self.__code_gen)] * 2,
                                                     _gen.Linkage.EXTERNAL)
        op_result = self.__builder.call(op_func, [left_value, right_value])
        ref_counter.ref_decr(left_value)
        ref_counter.ref_decr(right_value)
        self.push(None, op_result)

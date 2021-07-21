import ast
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen
import flyable.data.lang_type as lang_type
import flyable.code_gen.caller as caller
import flyable.parse.op as parse_op


def bin_op(visitor, op, type_left, value_left, type_right, value_right):
    builder = visitor.get_builder()
    if type_left.is_obj() or type_left.is_python_obj() or type_left.is_collection() or type_right.is_obj() or type_right.is_python_obj() or type_right.is_collection():
        args_types = [type_left, type_right]
        args = [value_left, value_right]
        return caller.call_obj(visitor, parse_op.get_op_func_call(op), value_left, type_left, args, args_types)
    elif isinstance(op, ast.Add):
        return type_left, builder.add(value_left, value_right)
    elif isinstance(op, ast.Sub):
        return type_left, builder.sub(value_left, value_right)
    elif isinstance(op, ast.Mult):
        return type_left, builder.mul(value_left, value_right)
    elif isinstance(op, ast.Div):
        return type_left, builder.div(value_left, value_right)
    elif isinstance(op, ast.FloorDiv):
        if type_left.is_int() and type_right.is_int():
            result = builder.div(value_left, value_right)
            return lang_type.get_int_type(), result
        elif type_left.is_dec() or type_right.is_dec():
            value_right = builder.float_cast(value_right, code_type.get_double())  # cast in case it's not double
            value_left = builder.float_cast(value_left, code_type.get_double())  # cast in case it's not double
            result = builder.div(value_left, value_right)
            result = builder.int_cast(result, code_type.get_int64())
            result = builder.float_cast(result, code_type.get_double())
            return lang_type.get_dec_type(), result
    else:
        raise ValueError("Unsupported Op " + str(op))


def cond_op(visitor, op, type_left, first_value, type_right, second_value):
    builder = visitor.get_builder()
    if type_left.is_obj() or type_left.is_python_obj() or type_left.is_collection() or type_right.is_obj() or type_right.is_python_obj() or type_right.is_collection():
        args_types = [type_left, type_right]
        args = [first_value, second_value]
        return caller.call_obj(visitor, parse_op.get_op_func_call(op), first_value, type_left, args, args_types)
    elif isinstance(op, ast.And):
        return lang_type.get_bool_type(), builder.op_and(first_value, second_value)
    elif isinstance(op, ast.Or):
        return lang_type.get_bool_type(), builder.op_or(first_value, second_value)
    elif isinstance(op, ast.Eq):
        return lang_type.get_bool_type(), builder.eq(first_value, second_value)
    elif isinstance(op, ast.NotEq):
        return lang_type.get_bool_type(), builder.ne(first_value, second_value)
    elif isinstance(op, ast.Lt):
        return lang_type.get_bool_type(), builder.lt(first_value, second_value)
    elif isinstance(op, ast.LtE):
        return lang_type.get_bool_type(), builder.lte(first_value, second_value)
    elif isinstance(op, ast.Gt):
        return lang_type.get_bool_type(), builder.gt(first_value, second_value)
    elif isinstance(op, ast.GtE):
        return lang_type.get_bool_type(), builder.gte(first_value, second_value)
    else:
        raise NotImplementedError("Compare op not supported")


def unary_op(visitor, type, value, op):
    if type.is_obj() or type.is_python_obj() or type.is_collection():
        args_types = [type]
        args = [value]
        return caller.call_obj(visitor, parse_op.get_op_func_call(op), value, type, args, args_types)
    elif isinstance(op, ast.Not):
        return unary_op_not(visitor, type, value)
    elif isinstance(op, ast.Invert):
        return unary_op_invert(visitor, type, value)
    elif isinstance(op, ast.UAdd):
        return unary_op_uadd(visitor, type, value)
    elif isinstance(op, ast.USub):
        return unary_op_usub(visitor, type, value)


def unary_op_not(visitor, type, value):
    if type.is_obj() or type.is_python_obj() or type.is_collection():
        args_types = [type]
        args = [value]
        return caller.call_obj(visitor, "__not__", value, type, args, args_types)
    elif type.is_int():
        return lang_type.get_bool_type(), visitor.get_builder().eq(value, visitor.get_builder().const_int64(0))
    elif type.is_dec():
        return lang_type.get_bool_type(), visitor.get_builder().eq(value, visitor.get_builder().const_float64(0.0))
    elif type.is_bool():
        return lang_type.get_bool_type(), visitor.get_builder().eq(value, visitor.get_builder().const_int1(0))


def unary_op_invert(visitor, type, value):
    if type.is_obj() or type.is_python_obj() or type.is_collection():
        args_types = [type]
        args = [value]
        return caller.call_obj(visitor, "__not__", value, type, args, args_types)
    elif type.is_int():
        return lang_type.get_int_type(), visitor.get_builder().eq(value, visitor.get_builder().const_int64(0))
    elif type.is_dec():
        return unary_op_invert(visitor, lang_type.get_int_type(),
                               visitor.get_builder().int_cast(value, code_type.get_int64()))
    elif type.is_bool():
        return lang_type.get_int_type(), visitor.get_builder().eq(value, visitor.get_builder().const_int1(0))


def unary_op_uadd(visitor, type, value):
    if type.is_obj() or type.is_python_obj() or type.is_collection():
        args_types = [type]
        args = [value]
        return caller.call_obj(visitor, "__pos__", value, type, args, args_types)
    elif type.is_int():
        abs_args = [code_type.get_int64(), code_type.get_int1()]
        abs_func = visitor.get_code_gen().get_or_create_func("llvm.abs.i64", code_type.get_int64(), abs_args,
                                                             gen.Linkage.EXTERNAL)
        return visitor.get_builder().call(abs_func, [value, visitor.get_builder().const_int1(0)])
    elif type.is_dec():
        abs_args = [code_type.get_double()]
        abs_func = visitor.get_code_gen().get_or_create_func("llvm.fabs.f64", code_type.get_double(), abs_args,
                                                             gen.Linkage.EXTERNAL)
        return visitor.get_builder().call(abs_func, [value])
    elif type.is_bool():
        return lang_type.get_int_type(), visitor.get_builder().eq(value, visitor.get_builder().const_int1(0))


def unary_op_usub(visitor, type, value):
    if type.is_obj() or type.is_python_obj() or type.is_collection():
        args_types = [type]
        args = [value]
        return caller.call_obj(visitor, "__neg__", value, type, args, args_types)
    elif type.is_int():
        abs_args = [code_type.get_int64(), code_type.get_int1()]
        abs_func = visitor.__code_gen.get_or_create_func("llvm.abs.i64", code_type.get_int64(), abs_args,
                                                         gen.Linkage.EXTERNAL)
        result = visitor.get_builder().call(abs_func, [value, visitor.get_builder().const_int1(0)])
        return lang_type.get_int_type(), visitor.get_builder().neg(result)
    elif type.is_dec():
        abs_args = [code_type.get_double()]
        abs_func = visitor.__code_gen.get_or_create_func("llvm.fabs.f64", code_type.get_double(), abs_args,
                                                         gen.Linkage.EXTERNAL)
        result = visitor.get_builder().call(abs_func, [value])
        return lang_type.get_dec_type(), visitor.get_builder().neg(result)
    elif type.is_bool():
        raise NotImplementedError()
        # return lang_type.get_int_type(), result


def bool_op(visitor, op, left_type, left_value, right_type, right_value):
    if isinstance(op, ast.And):
        return bool_op_and(visitor, left_type, left_value, right_type, right_value)
    elif isinstance(op, ast.Or):
        return bool_op_or(visitor, left_type, left_value, right_type, right_value)
    else:
        raise NotImplementedError(str(op))


def bool_op_and(visitor, left_type, left_value, right_type, right_value):
    if left_type.is_obj() or left_type.is_python_obj() or left_type.is_collection():
        args_types = [left_type, right_type]
        args = [left_value, right_value]
        return caller.call_obj(visitor, "__and__", left_value, left_type, args, args_types)
    elif left_type.is_primitive():
        return lang_type.get_bool_type(), visitor.get_builder()._and(left_value, right_value)
    elif left_type.is_obj() or left_type.is_python_obj() or left_type.is_list() or left_type.is_dict():
        types = [left_type, right_type]
        values = [left_value, right_value]
        return caller.call_obj(visitor, "__and__", left_value, left_type, values, types)
    else:
        raise NotImplementedError()


def bool_op_or(visitor, left_type, left_value, right_type, right_value):
    if left_type.is_obj() or left_type.is_python_obj() or left_type.is_collection():
        args_types = [left_type, right_type]
        args = [left_value, right_value]
        return caller.call_obj(visitor, "__or__", left_value, left_type, args, args_types)
    elif left_type.is_primitive():
        return lang_type.get_bool_type(), visitor.get_builder()._or(left_value, right_value)
    elif left_type.is_obj() or left_type.is_python_obj() or left_type.is_list() or left_type.is_dict():
        types = [left_type, right_type]
        values = [left_value, right_value]
        return caller.call_obj(visitor, "__or__", left_value, left_type, values, types)
    else:
        raise NotImplementedError()

import ast
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen
import flyable.data.lang_type as lang_type
import flyable.code_gen.caller as caller
import flyable.parse.op as parse_op


def bin_op(code_gen, builder, parser, op, type_left, value_left, type_right, value_right):
    if type_left.is_obj() or type_left.is_python_obj() or type_left.is_collection():
        args_types = [type_left, type_right]
        args = [value_left, value_right]
        return caller.call_obj(code_gen, builder, parser, parse_op.get_op_func_call(op), value_left, type_left, args,
                               args_types)
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


def unary_op(code_gen, builder, parser, type, value, op):
    if type.is_obj() or type.is_python_obj() or type.is_container():
        args_types = [type]
        args = [value]
        return caller.call_obj(code_gen, builder, parser, parse_op.get_op_func_call(op), value, type, args, args_types)
    elif isinstance(op, ast.Not):
        return unary_op_not(code_gen, builder, parser, type, value)
    elif isinstance(op, ast.Invert):
        return unary_op_invert(code_gen, builder, parser, type, value)
    elif isinstance(op, ast.UAdd):
        return unary_op_uadd(code_gen, builder, parser, type, value)
    elif isinstance(op, ast.USub):
        return unary_op_usub(code_gen, builder, parser, type, value)


def unary_op_not(code_gen, builder, parser, type, value):
    if type.is_obj() or type.is_python_obj() or type.is_collection():
        args_types = [type]
        args = [value]
        return caller.call_obj(code_gen, builder, parser, "__not__", value, type, args, args_types)
    elif type.is_int():
        return lang_type.get_bool_type(), builder.eq(code_gen, value, builder.const_int64(0))
    elif type.is_dec():
        return lang_type.get_bool_type(), builder.eq(code_gen, value, builder.const_float64(0.0))
    elif type.is_bool():
        return lang_type.get_bool_type(), builder.eq(code_gen, value, builder.const_int1(0))


def unary_op_invert(code_gen, builder, parser, type, value):
    if type.is_obj() or type.is_python_obj() or type.is_collection():
        args_types = [type]
        args = [value]
        return caller.call_obj(code_gen, builder, parser, "__not__", value, type, args, args_types)
    elif type.is_int():
        return lang_type.get_int_type(), builder.eq(code_gen, value, builder.const_int64(0))
    elif type.is_dec():
        return unary_op_invert(code_gen, builder, parser, lang_type.get_int_type(),
                               builder.int_cast(value, code_type.get_int64()))
    elif type.is_bool():
        return lang_type.get_int_type(), builder.eq(code_gen, value, builder.const_int1(0))


def unary_op_uadd(code_gen, builder, parser, type, value):
    if type.is_obj() or type.is_python_obj() or type.is_collection():
        args_types = [type]
        args = [value]
        return caller.call_obj(code_gen, builder, parser, "__pos__", value, type, args, args_types)
    elif type.is_int():
        abs_args = [code_type.get_int64(), code_type.get_int1()]
        abs_func = code_gen.get_or_create_func("llvm.abs.i64", code_type.get_int64(), abs_args, gen.Linkage.EXTERNAL)
        return builder.call(abs_func, [value, builder.const_int1(0)])
    elif type.is_dec():
        abs_args = [code_type.get_double()]
        abs_func = code_gen.get_or_create_func("llvm.fabs.f64", code_type.get_double(), abs_args, gen.Linkage.EXTERNAL)
        return builder.call(abs_func, [value])
    elif type.is_bool():
        return lang_type.get_int_type(), builder.eq(code_gen, value, builder.const_int1(0))


def unary_op_usub(code_gen, builder, parser, type, value):
    if type.is_obj() or type.is_python_obj() or type.is_collection():
        args_types = [type]
        args = [value]
        return caller.call_obj(code_gen, builder, parser, "__neg__", value, type, args, args_types)
    elif type.is_int():
        abs_args = [code_type.get_int64(), code_type.get_int1()]
        abs_func = code_gen.get_or_create_func("llvm.abs.i64", code_type.get_int64(), abs_args, gen.Linkage.EXTERNAL)
        result = builder.call(abs_func, [value, builder.const_int1(0)])
        return lang_type.get_int_type(), builder.neg(result)
    elif type.is_dec():
        abs_args = [code_type.get_double()]
        abs_func = code_gen.get_or_create_func("llvm.fabs.f64", code_type.get_double(), abs_args, gen.Linkage.EXTERNAL)
        result = builder.call(abs_func, [value])
        return lang_type.get_dec_type(), builder.neg(result)
    elif type.is_bool():
        raise NotImplementedError()
        # return lang_type.get_int_type(), result


def bool_op(op, code_gen, builder, parser, left_type, left_value, right_type, right_value):
    if isinstance(op, ast.And):
        return bool_op_and(code_gen, builder, left_type, left_value, right_type, right_value)
    elif isinstance(op, ast.Or):
        return bool_op_or(code_gen, builder, parser, left_type, left_value, right_type, right_value)
    else:
        raise NotImplementedError()


def bool_op_and(code_gen, builder, parser, left_type, left_value, right_type, right_value):
    if left_type.is_obj() or left_type.is_python_obj() or left_type.is_collection():
        args_types = [left_type, right_type]
        args = [left_value, right_value]
        return caller.call_obj(code_gen, builder, parser, "__and__", left_value, left_type, args, args_types)
    elif left_type.is_primitive():
        return lang_type.get_bool_type(), builder._and(left_value, right_value)
    elif left_type.is_obj() or left_type.is_python_obj() or left_type.is_list() or left_type.is_dict():
        types = [left_type, right_type]
        values = [left_value, right_value]
        return caller.call_obj(code_gen, builder, parser, "__and__", left_value, left_type, values, types)
    else:
        raise NotImplementedError()


def bool_op_or(code_gen, builder, left_type, parser, left_value, right_type, right_value):
    if left_type.is_obj() or left_type.is_python_obj() or left_type.is_collection():
        args_types = [left_type, right_type]
        args = [left_value, right_value]
        return caller.call_obj(code_gen, builder, parser, "__or__", left_value, left_type, args, args_types)
    elif left_type.is_primitive():
        return lang_type.get_bool_type(), builder._or(left_value, right_value)
    elif left_type.is_obj() or left_type.is_python_obj() or left_type.is_list() or left_type.is_dict():
        types = [left_type, right_type]
        values = [left_value, right_value]
        return caller.call_obj(code_gen, builder, parser, "__or__", left_value, left_type, values, types)
    else:
        raise NotImplementedError()

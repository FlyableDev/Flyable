import ast
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen


def bin_op(code_gen, builder, op, type_left, value_left, type_right, value_right):
    if isinstance(op, ast.Add):
        result = builder.add(value_left, value_right)
    elif isinstance(op, ast.Sub):
        result = builder.sub(value_left, value_right)
    elif isinstance(op, ast.Mult):
        result = builder.mul(value_left, value_right)
    elif isinstance(op, ast.Div):
        result = builder.div(value_left, value_right)
    elif isinstance(op, ast.FloorDiv):
        pass  # TODO: Support floor div
    else:
        raise ValueError("Unsupported Op " + str(op))
    return result


def unary_op(code_gen, builder, type, value, op):
    if isinstance(op, ast.Not):
        return unary_op_not(code_gen, builder, type, value)
    elif isinstance(op, ast.Invert):
        return unary_op_invert(code_gen, builder, type, value)
    elif isinstance(op, ast.UAdd):
        return unary_op_uadd(code_gen, builder, type, value)
    elif isinstance(op, ast.USub):
        return unary_op_usub(code_gen, builder, type, value)


def unary_op_not(code_gen, builder, type, value):
    if type.is_int():
        return builder.eq(code_gen, value, builder.const_int64(0))
    elif type.is_dec():
        return builder.eq(code_gen, value, builder.const_float64(0.0))
    elif type.is_bool():
        return builder.eq(code_gen, value, builder.const_int1(0))


def unary_op_invert(code_gen, builder, type, value):
    if type.is_int():
        return builder.eq(code_gen, value, builder.const_int64(0))
    elif type.is_dec():
        return builder.eq(code_gen, value, builder.const_float64(0.0))
    elif type.is_bool():
        return builder.eq(code_gen, value, builder.const_int1(0))


def unary_op_uadd(code_gen, builder, type, value):
    if type.is_int():
        abs_args = [code_type.get_int64(), code_type.get_int1()]
        abs_func = code_gen.get_or_create_func("llvm.abs.i64", code_type.get_int64(), abs_args, gen.Linkage.EXTERNAL)
        return builder.call(abs_func, [value, builder.const_int1(0)])
    elif type.is_dec():
        abs_args = [code_type.get_double()]
        abs_func = code_gen.get_or_create_func("llvm.fabs.f64", code_type.get_double(), abs_args, gen.Linkage.EXTERNAL)
        return builder.call(abs_func, [value])
    elif type.is_bool():
        return builder.eq(code_gen, value, builder.const_int1(0))


def unary_op_usub(code_gen, builder, type, value):
    if type.is_int():
        abs_args = [code_type.get_int64(), code_type.get_int1()]
        abs_func = code_gen.get_or_create_func("llvm.abs.i64", code_type.get_int64(), abs_args, gen.Linkage.EXTERNAL)
        result = builder.call(abs_func, [value, builder.const_int1(0)])
        return builder.neg(result)
    elif type.is_dec():
        abs_args = [code_type.get_double()]
        abs_func = code_gen.get_or_create_func("llvm.fabs.f64", code_type.get_double(), abs_args, gen.Linkage.EXTERNAL)
        result = builder.call(abs_func, [value])
        return builder.neg(result)
    elif type.is_bool():
        raise NotImplementedError()

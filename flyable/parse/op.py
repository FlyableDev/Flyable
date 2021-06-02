import ast


def is_op_cond(op):
    if isinstance(op, ast.Eq):
        return True
    elif isinstance(op, ast.NotEq):
        return True
    elif isinstance(op, ast.Lt):
        return True
    elif isinstance(op, ast.LtE):
        return True
    elif isinstance(op, ast.Gt):
        return True
    elif isinstance(op, ast.GtE):
        return True
    elif isinstance(op, ast.Is):
        return True
    elif isinstance(op, ast.IsNot):
        return True
    elif isinstance(op, ast.In):
        return True
    elif isinstance(op, ast.NotIn):
        return True
    return False


def get_op_func_call(op):
    """
    Convert an operator into the right python func call
    """
    result = ""
    if isinstance(op, ast.Add):
        result = "__add__"
    elif isinstance(op, ast.Sub):
        result = "__sub__"
    elif isinstance(op, ast.Div):
        result = "__div__"
    elif isinstance(op, ast.FloorDiv):
        result = "__floordiv"
    elif isinstance(op, ast.And):
        result = "and_"
    elif isinstance(op, ast.BitAnd):
        result = "__and__"
    elif isinstance(op, ast.Or):
        result = "or_"
    elif isinstance(op, ast.BitOr):
        result = "__or__"
    elif isinstance(op, ast.BitXor):
        result = "__xor__"
    elif isinstance(op, ast.Pow):
        result = "__pow__"
    elif isinstance(op, ast.LShift):
        result = "__lshift__"
    elif isinstance(op, ast.RShift):
        result = "__rshift__"
    elif isinstance(op, ast.Mod):
        result = "__mod__"
    elif isinstance(op, ast.Mult):
        result = "__mul__"
    elif isinstance(op, ast.MatMult):
        result = "__mul__"
    elif isinstance(op, ast.Eq):
        result = "__eq__"
    elif isinstance(op, ast.NotEq):
        result = "__ne__"
    elif isinstance(op, ast.Lt):
        result = "__lt__"
    elif isinstance(op, ast.LtE):
        result = "__le__"
    elif isinstance(op, ast.Gt):
        result = "__gt__"
    elif isinstance(op, ast.GtE):
        result = "__ge__"
    elif isinstance(op, ast.Is):
        result = "__is__"
    elif isinstance(op, ast.IsNot):
        result = "__is_not__"  # TODO: Confirm the op
    elif isinstance(op, ast.In):
        result = "__in__"
    elif isinstance(op, ast.NotIn):
        result = "__not_in__"  # Todo: Confirm the op

import ast


def is_op_cond(op: ast.operator):
    return op.__class__ in {
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.Is,
        ast.IsNot,
        ast.In,
        ast.NotIn,
    }


def is_op_cond_special_case(op: ast.operator):
    return op.__class__ in {ast.NotIn, ast.Is, ast.IsNot}


def get_op_func_call(op: ast.operator):
    """
    Convert an operator into the right python func call\n

    WARNING The operator 'In' is a special case. Because the __contains__ method doesn't behave
    like other dunder methods\n
    >>> 'a' in 'abc' == 'abc'.__contains__('a')\n
    it must be handled on it's own
    """
    if is_op_cond_special_case(op):
        raise ValueError(
            f"The operator '{op.__class__.__name__}' is a special case and doesn't have a "
            f"dunder method associated to it"
        )

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

    elif isinstance(op, ast.In):
        """SPECIAL CASE: SEE FUNCTION DOCSTRING!"""
        result = "__contains__"

    return result

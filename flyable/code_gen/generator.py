import flyable.code_gen.code_type as code_type
from flyable.code_gen.code_gen import CodeGen, CodeBuilder, Linkage

"""
Code generation functionality related to generators.
"""


def flyable_handle_return_generator_bytecode(
    code_gen: CodeGen, builder: CodeBuilder
) -> int:
    """handles return_generator bytecode

    Args:
        code_gen (CodeGen): code_gen
        builder (CodeBuilder): builder

    Returns:
        int: generator
    """
    func_name = "flyable_handle_return_generator_bytecode"
    func_call = code_gen.get_or_create_func(
        func_name, code_type.get_py_obj_ptr(code_gen), [], Linkage.EXTERNAL
    )
    return builder.call(func_call, [])

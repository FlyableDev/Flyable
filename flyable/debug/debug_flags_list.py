"""
Module where are declared the diffenrent debug flags
"""
from typing import Literal

from flyable.debug.debug_flags import DebugFlag

"""
Conventions:
1. Debug flag's name must start with FLAG_
2. Every debug flag must be type hinted
3. If the flag can have value, set default_value in the constructor to avoid errors 

template with value: 
    FLAG_<name>: DebugFlag[<type>] = DebugFlag(default_value=<value>)
template without value:
    FLAG_<name>: DebugFlag = DebugFlag()
"""

FLAG_SHOW_VISIT_AST: DebugFlag[int] = DebugFlag(default_value=2)

FLAG_SHOW_OUTPUT_BUILDER: DebugFlag = DebugFlag()

FLAG_SHOW_OPCODE_ON_EXEC: DebugFlag = DebugFlag()
"""Used to tell it's a debug build or not"""

FLAG_SHOW_BLOCK_BRANCHES: DebugFlag[str] = DebugFlag(default_value="basic")
"""Precision level: "all" | "basic" """

FLAG_PRINT_FUNC_IMPL: DebugFlag = DebugFlag()
FLAG_PRINT_INT64: DebugFlag = DebugFlag()

FLAG_LOG_DEBUG: DebugFlag[str] = DebugFlag(default_value="./debug.log")
"""value: str (path of log file)"""

FLAG_SHOW_STEP_LEVEL: DebugFlag[int] = DebugFlag(default_value=1)

FLAGS = {flag_name: flag for flag_name, flag in locals().items() if flag_name.startswith("FLAG_")}
"""
Here is a dictionnary containing all the flags so you can access them programmatically.

WARNING
    the keys of this dictionnary are the name of the variable of the debug FLAGs.\n
    If you change the name of a variable, it changes the name of the flag inside this dictionary\n
    Proceed with caution 
(~°3°)~
"""


def get_enabled_debug_flags() -> list[DebugFlag]:
    return [flag for flag in FLAGS.values() if flag.is_enabled]


def get_all_debug_flags() -> list[DebugFlag]:
    return list(FLAGS.values())


def get_flag(name: str, default=None) -> DebugFlag:
    return FLAGS.get(name, default)


def get_flag_name(flag: DebugFlag):
    return next((flag_name for flag_name, debug_flag in FLAGS.items() if flag is debug_flag), None)

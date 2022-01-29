"""
Module where are declared the diffenrent debug flags
"""

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

FLAG_SHOW_BLOCK_BRANCHES: DebugFlag = DebugFlag()
FLAG_PRINT_FUNC_IMPL: DebugFlag = DebugFlag()
FLAG_PRINT_INT64: DebugFlag = DebugFlag()

FLAG_LOG_DEBUG: DebugFlag[str] = DebugFlag(default_value="./debug.log")
"""value: str (path of log file)"""

FLAG_SHOW_STEP_LEVEL: DebugFlag[int] = DebugFlag(default_value=1)

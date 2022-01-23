from __future__ import annotations

from enum import Enum, auto


class DebugFlags(Enum):
    """Enum where are defined the different debug flags that can be toggle on and off"""

    SHOW_VISIT_AST = auto()
    SHOW_OUTPUT_BUILDER = auto()
    SHOW_OPCODE_ON_EXEC = auto()
    PRINT_FUNC_IMPL = auto()

    @classmethod
    def enable_debug_flags(cls, *debug_flags: DebugFlags):
        """Method to toggle on multiple debug flags easly"""
        for debug_flag in debug_flags:
            debug_flag.__is_enabled = True

    @classmethod
    def disable_debug_flags(cls, *debug_flags: DebugFlags):
        """Method to toggle off multiple debug flags easly"""
        for debug_flag in debug_flags:
            debug_flag.__is_enabled = False

    @classmethod
    def get_enabled_debug_flags(cls) -> list[DebugFlags]:
        return [flag for flag in cls.__members__.values() if flag.is_enabled]

    @classmethod
    def get_all_debug_flags(cls) -> list[str]:
        return list(cls.__members__.keys())

    def __init__(self, *_) -> None:
        """Constructor that sets the property is_enabled to False"""
        super().__init__()
        self.__is_enabled = False

    @property
    def is_enabled(self):
        return self.__is_enabled

    def __str__(self) -> str:
        return f"{self.name}={self.is_enabled}"


def value_if_debug(normal_value, debug_value, flag: DebugFlags):
    """Convenience function that return the normal value if the flag is not enabled and the debug value if it is

    Args:
        normal_value (? extends T): Value to be returned if the debug flag is not enabled
        debug_value (? extends T): Value to be returned if the debug flag is enabled
        flag (DebugFlags): Flag to inspect

    Returns:
        T: Either the normal value or the debug value, depending if the flag is enabled
    """
    if flag.is_enabled:
        return debug_value
    else:
        return normal_value


def debug_flag_enabled(flag: DebugFlags):
    return flag.is_enabled

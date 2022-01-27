from __future__ import annotations

from enum import Enum, auto
from typing import Callable


class DebugFlags(Enum):
    """Enum where are defined the different debug flags that can be toggle on and off"""

    SHOW_VISIT_AST = auto()
    SHOW_OUTPUT_BUILDER = auto()
    SHOW_OPCODE_ON_EXEC = auto()
    PRINT_FUNC_IMPL = auto()
    PRINT_INT64 = auto()

    STEP_LEVEL = 1
    """STEP_LEVEL: Value range between 0 and 4"""

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


def get_flag_value(flag: DebugFlags):
    return flag.value


def value_if_debug(
        normal_value, debug_value, flag: DebugFlags, condition: Callable = None
):
    """Convenience function that returns the normal value if the flag is not enabled or the flag's value doesn't meet
    the requirements and returns the debug value if it is enabled and its value meets the requirements

    Example:
        value_if_debug("hello", "world", DebugFlags.STEP_LEVEL, lambda level: level >= 2)

        value_if_debug("foo", "bar", DebugFlags.SHOW_VISIT_AST)

    :param normal_value: (? extends T): Value to be returned if the debug flag is not enabled
    :param debug_value: (? extends T): Value to be returned if the debug flag is enabled
    :param flag: (DebugFlags): Flag to inspect
    :param condition: (Callable): predicate condition for the flag value (optionnal)

    :returns: Either the normal value or the debug value, depending if the flag is enabled
    """
    if flag.is_enabled and (condition is None or condition(flag.value)):
        return debug_value
    else:
        return normal_value


def do_if_debug(
        func: Callable,
        flag: DebugFlags,
        args: tuple = (),
        kwargs: dict = None,
        condition: Callable = None,
):
    """Convenience function that calls a function if the flag is enabled and the flag's value meets the requirements

    Example:
        do_if_debug(print, args=("hello", "world"), kwargs={"sep": "\\\\n"}, flag=DebugFlags.STEP_LEVEL,
        condition=lambda level: level >= 2)
        do_if_debug(input, args=("Enter your message",) DebugFlags.SHOW_VISIT_AST)

    :param func: (Callable): function to call if the flag is enabled
    :param args: (tuple): args to the function
    :param kwargs: (dict): kwargs to the function
    :param flag: (DebugFlags): Flag to inspect
    :param condition: (Callable): predicate condition for the flag value (optionnal)

    :returns: Either the normal value or the debug value, depending if the flag is enabled
    """
    if flag.is_enabled and (condition is None or condition(flag.value)):
        kwargs = kwargs if kwargs is not None else {}
        return func(*args, **kwargs)


def debug_flag_enabled(flag: DebugFlags):
    return flag.is_enabled

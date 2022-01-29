from __future__ import annotations

from dataclasses import dataclass, field

from typing import Callable, Generic, TypeVar, Optional, TypeAlias

T = TypeVar("T")

_DEBUG_FLAGS_LIST: list[DebugFlag] = []
DebugFlagListType: TypeAlias = "list[DebugFlag[T] | tuple[DebugFlag[T], T]]"


@dataclass
class DebugFlag(Generic[T]):
    """Class where are defined the properties of a debug flag"""

    default_value: Optional[T] = field(default=None)
    value: T = field(init=False)
    is_enabled: bool = field(default=False, init=False)

    def __post_init__(self):
        self.value = self.default_value
        _DEBUG_FLAGS_LIST.append(self)

    def enable(self, value: T = None):
        if value is not None:
            self.value = value
        self.is_enabled = True

    def disable(self):
        self.is_enabled = False
        self.value = self.default_value

    def __bool__(self):
        return self.is_enabled


def enable_debug_flags(*debug_flags: DebugFlag[T] | tuple[DebugFlag[T], T]):
    """Method to toggle on multiple debug flags easly"""
    for debug_flag in debug_flags:
        if isinstance(debug_flag, tuple):
            debug_flag[0].enable(debug_flag[1])
        else:
            debug_flag.enable()


def disable_debug_flags(*debug_flags: DebugFlag[T]):
    """Method to toggle off multiple debug flags easly"""
    for debug_flag in debug_flags:
        debug_flag.disable()


def get_enabled_debug_flags() -> list[DebugFlag]:
    return [flag for flag in _DEBUG_FLAGS_LIST if flag.is_enabled]


def get_all_debug_flags() -> list[DebugFlag]:
    return _DEBUG_FLAGS_LIST[:]


def value_if_debug(
        normal_value,
        debug_value,
        flag: DebugFlag[T],
        condition: Callable[[T], bool] = None,
):
    """Convenience function that returns the normal value if the flag is not enabled or the flag's value doesn't meet
    the requirements and returns the debug value if it is enabled and its value meets the requirements

    Example:
        >>> value_if_debug("hello", "world", SHOW_STEP_LEVEL, lambda level: level >= 2)

        >>> value_if_debug("foo", "bar", SHOW_VISIT_AST)

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
        flag: DebugFlag[T],
        args: tuple = (),
        kwargs: dict = None,
        condition: Callable[[T], bool] = None,
):
    """Convenience function that calls a function if the flag is enabled and the flag's value meets the requirements

    Example:
        >>> do_if_debug(print, args=("hello", "world"), kwargs={"sep": "\\n"}, flag=STEP_LEVEL, \
        condition=lambda level: level >= 2)
        >>> do_if_debug(input, args=("Enter your message",) SHOW_VISIT_AST)

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

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Type, Union

if TYPE_CHECKING:
    from flyable.data.lang_type import LangType
    from flyable.data.attribute import Attribut
    from flyable.parse.variable import Variable


class TypeHint:
    pass


def get_lang_type_contained_hint_type(lang_type: LangType, hint_type: Type[TypeHint]) -> Any:
    for hint in lang_type.get_hints():
        if isinstance(hint, hint_type):
            return hint
    return None


def remove_hint_type(lang_type: LangType, hint_type: Type[TypeHint]):
    for i, hint in enumerate(lang_type.get_hints()):
        if isinstance(hint, hint_type):
            lang_type.remove_hint(i)
            remove_hint_type(lang_type, hint_type)
            return True
    return False


"""
Const value hints
"""


def is_const_type(lang_type: LangType, const_type: type):
    found_hint = get_lang_type_contained_hint_type(lang_type, TypeHintConstValue)
    if found_hint is not None:
        return isinstance(found_hint.get_value(), const_type)
    return False


class TypeHintConstValue(TypeHint):

    def __init__(self, value: int | float | bool | str):
        self.__value = value

    def get_value(self):
        return self.__value


class TypeHintConstDec(TypeHintConstValue):
    def __init__(self, value: float):
        super().__init__(value)


class TypeHintConstInt(TypeHintConstValue):
    def __init__(self, value: int):
        super().__init__(value)


class TypeHintConstBool(TypeHintConstValue):
    def __init__(self, value: bool):
        super().__init__(value)


class TypeHintConstStr(TypeHintConstValue):
    def __init__(self, value: str):
        super().__init__(value)


class TypeHintCanBeNone(TypeHint):
    pass


"""
Type hints
"""


def is_python_type(lang_type: LangType, class_path: str):
    if lang_type.is_python_obj():
        found_hint = get_lang_type_contained_hint_type(lang_type, TypeHintPythonType)
        if found_hint is not None and isinstance(found_hint, TypeHintPythonType):
            return found_hint.get_class_path() == class_path
    return False


class TypeHintPythonType(TypeHint):
    """
    Hint representing the Python type represented.
    Used to cache functions
    """

    def __init__(self, class_path: str):
        self.__class_path = class_path

    def get_class_path(self):
        return self.__class_path


class TypeHintConstLen(TypeHint):
    """
    Hint representing a container (list, dict,tuple...) with a const len
    """

    def __init__(self, count: int):
        self.__count = count

    def get_count(self):
        return self.__count


class TypeHintCollectionContentHint(TypeHint):
    """
    Hint representing what content a collection has inside
    """

    def __init__(self, hint_type: LangType):
        self.__hint_type = hint_type

    def get_hint_type(self):
        return self.__hint_type

    def __str__(self):
        result = "<Collection contentHint " + str(self.__hint_type) + " >"
        return result


class TypeHintCollectionContentRange(TypeHint):
    """
    Hint representing what content collection has inside for a specific range of int
    """

    def __init__(self, minimum=0, maximum=0, type: LangType = None):
        self.__min_range: int = minimum
        self.__max_range: int = maximum
        self.__type = type

    def set_range(self, minimum: int, maximum: int):
        self.__min_range = minimum
        self.__max_range = maximum

    def get_min(self):
        self.__min_range

    def get_max(self):
        return self.__max_range

    def get_type(self):
        return self.__type


"""
Memory management hint
"""


def is_incremented_type(lang_type: LangType):
    """
    Return if the type contains the TypeHintRefIncr hints
    """
    return get_lang_type_contained_hint_type(lang_type, TypeHintRefIncr) is not None


class TypeHintRefIncr(TypeHint):
    """
    Hint that indicates that the type comes from an incremented source and will need to be decremented
    """
    pass


class TypeHintRefCount(TypeHint):
    """
    Hint that indicates how many counts there is on the item when the counts is known
    """

    def __init__(self, count: int):
        self.__count = count

    def get_count(self):
        return self.__count


"""
Data source hints
Gives hints from where the type comes from
"""


def get_type_source(hint_type: LangType):
    for e in hint_type.iter_hints():
        if isinstance(e, TypeHintDataSource):
            return e
    return None


class TypeHintDataSource(TypeHint):
    """
    Hint that indicates that the type comes from a data source
    """

    def __init__(self, var: Variable | Attribut):
        self.__source = var

    def get_source(self):
        return self.__source


class TypeHintSourceLocalVariable(TypeHintDataSource):
    """
    Hint that indicates that the type comes from a local variable
    """

    def __init__(self, var: Variable):
        super().__init__(var)


class TypeHintSourceAttribute(TypeHintDataSource):
    """
    Hint that indicates that the type comes from an object attribute
    """

    def __init__(self, attribute: Attribut):
        super().__init__(attribute)


"""
Range hints
"""


class TypeHintIntRange(TypeHint):
    """
    Hints that represents stuff
    """

    def __init__(self, minimum: int = 0, maximum: int = 0):
        self.__min_range = minimum
        self.__max_range = maximum

    def set_range(self, minimum: int, maximum: int):
        self.__min_range = minimum
        self.__max_range = maximum

    def get_min(self):
        self.__min_range

    def get_max(self):
        return self.__max_range

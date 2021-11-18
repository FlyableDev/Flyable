class TypeHint:
    pass


def get_lang_type_contained_hint_type(lang_type, hint_type):
    for hint in lang_type.get_hints():
        if isinstance(hint, hint_type):
            return hint
    return None


def remove_hint_type(lang_type, hint_type):
    for i, hint in enumerate(lang_type.get_hints()):
        if isinstance(hint, hint_type):
            lang_type.remove_hint(i)
            remove_hint_type(lang_type, hint_type)
            return True
    return False


"""
Const value hints
"""


class TypeHintConstValue(TypeHint):

    def __init__(self, value):
        self.__value = value

    def get_value(self):
        return self.__value


class TypeHintConstDec(TypeHintConstValue):
    def __init__(self, value):
        super().__init__(value)


class TypeHintConstInt(TypeHintConstValue):
    def __init__(self, value):
        super().__init__(value)


class TypeHintConstBool(TypeHintConstValue):
    def __init__(self, value):
        super().__init__(value)


class TypeHintConstStr(TypeHintConstValue):
    def __init__(self, value):
        super().__init__(value)


"""
Type hints
"""


def is_python_type(lang_type, class_path):
    if lang_type.is_python_obj():
        found_hint = get_lang_type_contained_hint_type(lang_type, TypeHintPythonType)
        if found_hint is not None:
            return found_hint.get_class_path() == class_path
    return False


class TypeHintPythonType(TypeHint):
    """
    Hint representing the Python type represented.
    Used to cache functions
    """

    def __init__(self, class_path):
        self.__class_path = class_path

    def get_class_path(self):
        return self.__class_path


class TypeHintConstLen(TypeHint):
    """
    Hint representing a container (list, dict,tuple...) with a const len
    """

    def __init__(self, count):
        self.__count = count

    def get_count(self):
        return self.__count


"""
Memory management hint
"""


def is_incremented_type(lang_type):
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

    def __init__(self, count):
        self.__count = count

    def get_count(self):
        return self.__count


"""
Data source hints
Gives hints from where the type comes from
"""


class TypeHintDataSource(TypeHint):
    """
    Hint that indicates that the type comes from a data source
    """
    pass


class TypeHintSourceLocalVariable(TypeHintDataSource):
    """
    Hint that indicates that the type comes from a local variable
    """

    def __init__(self, var):
        self.__var = var

    def get_var(self):
        return self.__var


class TypeHintSourceAttribute(TypeHintDataSource):
    """
    Hint that indicates that the type comes from an object attribute
    """

    def __init__(self, attribute):
        self.__attribute = attribute

    def get_attribute(self):
        return self.__attribute

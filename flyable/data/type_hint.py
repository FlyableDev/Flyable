class TypeHint:
    pass


def get_lang_type_contained_hint_type(lang_type, hint_type):
    for hint in lang_type.get_hints():
        if isinstance(hint, hint_type):
            return hint
    return None


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


class TypeHintPythonType(TypeHint):
    """
    Hint representing the Python type represented.
    Used to cache functions
    """
    pass


class TypeHintConstLen(TypeHint):
    """
    Hint representing a container (list, dict,tuple...) with a const len
    """

    def __init__(self, count):
        self.__count = count

    def get_count(self):
        return self.__count

class TypeHint:
    pass


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

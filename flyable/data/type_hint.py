class TypeHint:
    pass


class TypeHintConstValue(TypeHint):

    def __init__(self, value):
        self.__value = value

    def get_value(self):
        return self.__value


class TypeHintConstDec(TypeHint):
    def __init__(self, value):
        super().__init__(value)


class TypeHintConstInt(TypeHint):
    def __init__(self, value):
        super().__init__(value)


class TypeHintConstStr(TypeHint):
    def __init__(self, value):
        super().__init__(value)


class TypeHintPythonType(TypeHint):
    pass


class TypeHintListSize(TypeHint):

    def __init__(self, count):
        self.__count = count

    def get_count(self):
        return self.__count

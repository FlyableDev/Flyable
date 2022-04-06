class Variable:

    def __init__(self, name):
        self.__name = name
        self.__code_value = None

    def get_name(self):
        return self.__name

    def set_code_value(self, value):
        self.__code_value = value

    def get_code_value(self):
        return self.__code_value

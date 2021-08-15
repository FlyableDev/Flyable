import flyable.data.lang_type as type


class Variable:

    def __init__(self, id=0):
        self.__id = id
        self.__name = ""
        self.__type = type.LangType()
        self.__is_initialized = False
        self.__in_use = True
        self.__code_gen_value = None
        self.__is_arg = False
        self.__global = False

    def get_id(self):
        return self.__id

    def set_name(self, name):
        self.__name = name

    def get_name(self):
        return self.__name

    def set_type(self, type):
        self.__type = type

    def get_type(self):
        return self.__type

    def set_use(self, used):
        self.__in_use = used

    def set_is_arg(self, arg):
        self.__is_arg = arg

    def is_arg(self):
        return self.__is_arg

    def set_code_gen_value(self, value):
        self.__code_gen_value = value

    def get_code_gen_value(self):
        return self.__code_gen_value

    def is_global(self):
        return self.__global

    def set_global(self, _global):
        self.__global = _global

    def is_used(self):
        return self.__in_use

    def set_initialized(self, init):
        self.__is_initialized = init

    def is_initialized(self):
        return self.__is_initialized

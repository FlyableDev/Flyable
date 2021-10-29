import copy

import flyable.data.lang_type as type
import flyable.parse.context as context
import flyable.data.type_hint as hint
import enum


class LangFuncImpl:
    """"
    Represents an actual implementation of a function.
    In most cases a function will generate two different sets of machine instructions.
    This class represent a concrete implementation of this.
    Example :

    def test(a,b): # This is a function definition
        return a + b

    test(10,20) # Generate one implementation of the code to add both int args
    test("a","b") # Generate another implementation of the code that calls __add__ from the str class
    """

    class ParseStatus(enum.IntEnum):
        NOT_STARTED = 0,
        STARTED = 1,
        ENDED = 1

    def __init__(self):
        self.__id = -1
        self.__unknown = False
        self.__code_func = None
        self.__args = []
        self.__parent_func = None

        self.__parse_status = LangFuncImpl.ParseStatus.NOT_STARTED

        self.__return_type = type.LangType()

        self.__context = context.Context()

        self.__can_raise = False

    def set_id(self, _id):
        self.__id = _id

    def get_id(self):
        return self.__id

    def add_arg(self, arg):
        arg = copy.deepcopy(arg)
        hint.remove_hint_type(arg, hint.TypeHintRefIncr)
        self.__args.append(arg)

    def get_arg(self, index):
        return self.__args[index]

    def get_args_count(self):
        return len(self.__args)

    def args_iter(self):
        return iter(self.__args)

    def set_parent_func(self, parent):
        self.__parent_func = parent

    def get_parent_func(self):
        return self.__parent_func

    def set_unknown(self, unknown):
        self.__unknown = unknown

    def is_unknown(self):
        return self.__unknown

    def set_parse_status(self, status):
        return self.__parse_status

    def get_parse_status(self):
        return self.__parse_status

    def get_return_type(self):
        return self.__return_type

    def set_return_type(self, return_type):
        return_type = copy.deepcopy(return_type)
        hint.remove_hint_type(return_type, hint.TypeHintRefIncr)
        self.__return_type = return_type

    def set_code_func(self, func):
        self.__code_func = func

    def get_code_func(self):
        return self.__code_func

    def get_context(self):
        return self.__context

    def set_can_raise(self, can_raise):
        """
        Set if the implementation can potentially raise an exception during his execution
        """
        self.__can_raise = can_raise

    def can_raise(self):
        """
        Return if the implementation can potentially raise an exception during his execution
        """
        return self.__can_raise

    def __str__(self):
        result = str(self.__return_type) + " : "
        for e in self.__args:
            result += " " + str(e)
        return result

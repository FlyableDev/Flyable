import copy
from typing import List

import flyable.data.lang_type as type
import flyable.parse.context as context
import flyable.data.type_hint as hint
import enum


class FuncImplType(enum.IntEnum):
    NOT_IMPL = 0
    SPECIALIZATION = 1,
    VEC_CALL = 2,
    TP_CALL = 3


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
        self.__id: int = -1
        self.__unknown: bool = False
        self.__code_func = None
        self.__args: List[type.LangType] = []
        self.__parent_func = None

        self.__parse_status = LangFuncImpl.ParseStatus.NOT_STARTED

        self.__return_type: type.LangType = type.LangType()

        self.__context: context.Context = context.Context()

        self.__can_raise: bool = False

        self.__has_yield: bool = False

        self.__impl_type: FuncImplType = FuncImplType.NOT_IMPL

    def set_id(self, _id: int):
        self.__id = _id

    def get_id(self):
        return self.__id

    def set_impl_type(self, impl):
        self.__impl_type = impl

    def get_impl_type(self):
        return self.__impl_type

    def add_arg(self, arg: type.LangType):
        arg = copy.deepcopy(arg)
        hint.remove_hint_type(arg, hint.TypeHintRefIncr)
        self.__args.append(arg)

    def get_arg(self, index: int):
        return self.__args[index]

    def get_args(self):
        return copy.copy(self.__args)

    def get_args_count(self):
        return len(self.__args)

    def args_iter(self):
        return iter(self.__args)

    def set_parent_func(self, parent):
        self.__parent_func = parent

    def get_parent_func(self):
        return self.__parent_func

    def set_unknown(self, unknown: bool):
        self.__unknown = unknown

    def is_unknown(self):
        return self.__unknown

    def set_parse_status(self, status: ParseStatus):
        self.__parse_status = status

    def get_parse_status(self):
        return self.__parse_status

    def get_return_type(self):
        return self.__return_type

    def set_return_type(self, return_type: type.LangType):
        return_type = copy.deepcopy(return_type)
        hint.remove_hint_type(return_type, hint.TypeHintRefIncr)
        self.__return_type = return_type

    def set_code_func(self, func):
        self.__code_func = func

    def get_code_func(self):
        return self.__code_func

    def get_context(self):
        return self.__context

    def set_can_raise(self, can_raise: bool):
        """
        Set if the implementation can potentially raise an exception during his execution
        """
        self.__can_raise = can_raise

    def can_raise(self):
        """
        Return if the implementation can potentially raise an exception during his execution
        """
        return self.__can_raise

    def set_yield(self, _yield: bool):
        """
        Set if the function contains a yield
        """
        self.__has_yield = _yield

    def has_yield(self):
        """
        Returns if the function contains a yield. It might contain one and return False if it has not been visited yet
        """
        return self.__has_yield

    def clear_info(self):
        # We need to keep global variable for global funcs
        if not self.get_parent_func().is_global():
            self.__context = context.Context()
        self.__code_func = None

    def __str__(self):
        result = str(self.__return_type) + " : "
        for e in self.__args:
            result += " " + str(e)
        return result

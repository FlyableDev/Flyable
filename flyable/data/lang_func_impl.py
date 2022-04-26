from __future__ import annotations

import copy
from typing import List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from flyable.code_gen.code_gen import CodeFunc
    from flyable.data.lang_func import LangFunc

import flyable.data.lang_type as type
import flyable.parse.context as context
import flyable.data.type_hint as hint
import flyable.code_gen.code_type as code_type
import enum
import flyable.data.lang_type as lang_type


class FuncImplType(enum.IntEnum):
    NOT_IMPL = 0
    SPECIALIZATION = 1,
    VEC_CALL = 2,
    TP_CALL = 3


class LangFuncImpl:
    """
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
        ENDED = 2

    def __init__(self):
        self.__id: int = -1
        self.__code_func: CodeFunc | None = None
        self.__args: list[type.LangType] = []
        self.__parent_func: LangFunc | None = None

        self.__parse_status = LangFuncImpl.ParseStatus.NOT_STARTED

        self.__context: context.Context = context.Context()

        self.__impl_type: FuncImplType = FuncImplType.NOT_IMPL

    def set_id(self, _id: int):
        self.__id = _id

    def get_id(self):
        return self.__id

    def set_impl_type(self, impl: FuncImplType):
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

    def set_parent_func(self, parent: LangFunc):
        self.__parent_func = parent

    def get_parent_func(self):
        if self.__parent_func is None:
            raise Exception(f"Function implementation has no parent function")
        return self.__parent_func

    def set_parse_status(self, status: ParseStatus):
        self.__parse_status = status

    def get_parse_status(self):
        return self.__parse_status

    def set_code_func(self, func: CodeFunc):
        self.__code_func = func

    def get_code_func(self):
        return self.__code_func

    def get_context(self):
        return self.__context

    def get_return_type(self):
        return lang_type.get_python_obj_type()

    def clear_info(self):
        # We need to keep global variable for global funcs
        parent_func = self.get_parent_func()
        if parent_func is None:
            raise Exception("Could not clear info of function implementation due to missing parent function")

        if not parent_func.is_global():
            self.__context = context.Context()
        else:
            self.__context.clear_info()
        self.__code_func = None

    def get_code_func_args_signature(self, gen):
        if self.__impl_type == FuncImplType.TP_CALL:
            return [code_type.get_py_obj_ptr(gen)] * 3
        elif self.__impl_type == FuncImplType.VEC_CALL:
            return [code_type.get_py_obj_ptr(gen), code_type.get_py_obj_ptr(gen).get_ptr_to(), code_type.get_int64(),
                    code_type.get_py_obj_ptr(gen)]
        else:
            raise ValueError("Valid type expected to get signature")

    def get_full_name(self):
        extension = ""
        if self.get_impl_type() == FuncImplType.TP_CALL:
            extension = "@tp@"
        elif self.get_impl_type() == FuncImplType.VEC_CALL:
            extension = "@vec@"
        elif self.get_impl_type() == FuncImplType.SPECIALIZATION:
            extension = "@spec@"
        else:
            raise ValueError("Valid impl type expected")
        return self.__parent_func.get_name() + extension

    def __str__(self):
        result = str(self.__return_type) + " : "
        for e in self.__args:
            result += " " + str(e)
        return result

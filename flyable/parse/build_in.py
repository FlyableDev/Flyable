"""
Module managing all functions
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flyable.parse.parser_visitor import ParserVisitor
    from flyable.data.lang_type import LangType

from abc import ABC, abstractmethod

import flyable.code_gen.runtime as runtime
import flyable.data.lang_type as lang_type
import flyable.code_gen.list as gen_list


def get_build_in_name(name):
    import builtins as built_in
    try:
        return getattr(built_in, name)
    except AttributeError:
        return None


class BuildInFunc(ABC):

    def __init__(self):
        """Initialize the buildin function"""

    @abstractmethod
    def parse(self, args_types: list[LangType], args: list, visitor: ParserVisitor) -> tuple[LangType, int]:
        """Parses the function"""


class BuildInList(BuildInFunc):

    def __init__(self):
        super().__init__()

    def parse(self, args_types, args, visitor):
        if len(args_types) == 0:
            list_type = lang_type.get_list_of_python_obj_type()
            codegen = visitor.get_code_gen()
            builder = visitor.get_builder()
            return list_type, gen_list.instanciate_python_list(codegen, builder, builder.const_int64(0))


class BuildInLen(BuildInFunc):

    def __init__(self):
        super().__init__()

    def parse(self, args_types, args, visitor):
        if len(args_types) == 1 and args_types[0].is_list():
            return lang_type.get_int_type(), gen_list.python_list_len(visitor, args[0])
        else:
            return lang_type.get_int_type(), runtime.py_runtime_obj_len(visitor.get_code_gen(), visitor.get_builder(),
                                                                        args[0])


class BuildInInt(BuildInFunc):

    def __init__(self):
        super().__init__()

    def parse(self, args_types, args, visitor):
        if len(args_types) == 1 and args_types[0].is_str():
            return lang_type.get_int_type(), gen_list.python_list_len(visitor, args[0])
        else:
            return lang_type.get_int_type(), runtime.py_runtime_obj_len(visitor.get_code_gen(), visitor.get_builder(),
                                                                        args[0])


def get_build_in(name):
    name = str(name)
    build_in_funcs = {
        "list": BuildInList,
        "len": BuildInLen,
        "int": BuildInFunc
    }

    if name in build_in_funcs:
        return build_in_funcs[name]()  # Create an instance of the build-in class
    return get_build_in_name(name)  # Not implemented

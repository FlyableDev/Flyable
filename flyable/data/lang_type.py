from __future__ import annotations
from functools import reduce
import copy
from enum import Enum
from typing import TYPE_CHECKING, Union
from typing import Type as PyType
from flyable.code_gen.code_type import CodeType
import flyable.code_gen.code_type as code_type
import flyable.data.type_hint as hint
import flyable.code_gen.code_gen as code_gen

if TYPE_CHECKING:
    from flyable.data.comp_data import CompData


def to_code_type(code_gen: code_gen.CodeGen, type: Union[LangType, list[LangType]]):
    """
    Convert a list of LangType to a list of CodeType
    Or
    Convert a single LangType to a CodeType
    """
    if isinstance(type, list):
        result: list[CodeType] = []
        for e in type:
            result.append(e.to_code_type(code_gen))
        return result

    return type.to_code_type(code_gen)


def _get_type_common(primary_type: LangType, second_type: LangType = None) -> LangType:
    result: LangType
    if primary_type == second_type or second_type is None:
        result = copy.copy(primary_type)
    elif primary_type.is_python_obj() or second_type.is_python_obj():
        result = get_python_obj_type()
    elif primary_type.is_obj() and second_type.is_obj():
        result = get_python_obj_type()
    elif primary_type.is_none() or second_type.is_none():
        result = get_python_obj_type()
    elif primary_type.is_primitive() or second_type.is_primitive():
        # If one of them is primitive but they are not equals, only a py object can represent both
        result = get_python_obj_type()
    else:
        raise NotImplementedError()
    return result


def get_most_common_type(data, *types: LangType) -> LangType:
    """Finds a type that can contains all the types passed in
    the argument or returns None if there isn't one.

    Args:
        data ([type]): ??
        types (LangType...): the types you want to find the most common type

    Raises:
        ValueError: If there are not at least one type passed in the argument

    Returns:
        LangType: the most common type of all the types passed in the argument
    """
    if len(types) == 0:
        raise ValueError("You must specify at least one type to get the most common one")
    return reduce(_get_type_common, types[1:], types[0])


def get_int_type():
    return LangType(LangType.Type.INTEGER)


def get_dec_type():
    return LangType(LangType.Type.DECIMAL)


def get_bool_type():
    return LangType(LangType.Type.BOOLEAN)


def get_python_obj_type(obj_hint: Union[hint.TypeHint, list[hint.TypeHint]] = None):
    result = LangType(LangType.Type.PYTHON)

    if isinstance(obj_hint, list):
        for e in obj_hint:
            result.add_hint(e)
    elif isinstance(obj_hint, hint.TypeHint):
        result.add_hint(obj_hint)

    return result


def get_obj_type(id: int):
    return LangType(LangType.Type.OBJECT, id)


def get_module_type():
    return LangType(LangType.Type.MODULE)


def get_none_type():
    return LangType(LangType.Type.NONE)


def get_str_type():
    return get_python_obj_type(hint.TypeHintPythonType("builtins.str"))


def get_list_of_python_obj_type():
    return get_python_obj_type(hint.TypeHintPythonType("builtins.list"))


def get_tuple_of_python_obj_type():
    return get_python_obj_type(hint.TypeHintPythonType("builtins.tuple"))


def get_set_of_python_obj_type():
    return get_python_obj_type(hint.TypeHintPythonType("builtins.set"))


def get_dict_of_python_obj_type():
    return get_python_obj_type(hint.TypeHintPythonType("builtins.dict"))


def get_unknown_type():
    return LangType(LangType.Type.UNKNOWN)

def from_code_type(code_type: CodeType):
    import flyable.data.lang_type as lang_type
    if code_type.get_type() == CodeType.CodePrimitive.INT64:
        return lang_type.get_int_type()
    elif code_type.get_type() == CodeType.CodePrimitive.STRUCT:
        return lang_type.get_python_obj_type()
    elif code_type.get_type() == CodeType.CodePrimitive.DOUBLE:
        return lang_type.get_dec_type()
    elif code_type.get_type() == CodeType.CodePrimitive.FLOAT:
        return lang_type.get_dec_type()
    elif code_type.get_type() == CodeType.CodePrimitive.INT1:
        return lang_type.get_bool_type()
    elif code_type.get_type() == CodeType.CodePrimitive.VOID:
        return lang_type.get_none_type()

class LangType:
    class Type(Enum):
        UNKNOWN = 0,  # Type information may exist but unsure yet
        INTEGER = 1,  # Standard integer
        DECIMAL = 2,  # Standard floating point
        OBJECT = 3,  # A python object, __id represents the class of the instance
        MODULE = 4,  # Module object
        SUPER = 5,  # 'super()' call return a specific type of the object
        PYTHON = 6,  # Pure python object
        BOOLEAN = 7,  # Boolean value
        NONE = 8  # The None keyword

    def __init__(self, type: Type = Type.UNKNOWN, id: int = 0):
        if not isinstance(id, int):
            raise TypeError("Integer expected for id")

        self.__type: LangType.Type = type
        self.__id: int = id
        # Hints are extra data that allows the compiler to perform more severe optimization
        self.__hints: list[hint.TypeHint] = []

    def is_unknown(self):
        return self.__type == LangType.Type.UNKNOWN

    def is_list(self):
        return self.is_python_obj("builtins.list")

    def is_dict(self):
        return self.is_python_obj("builtins.dict")

    def is_set(self):
        return self.is_python_obj("builtins.set")

    def is_tuple(self):
        return self.is_python_obj("builtins.tuple")

    def is_collection(self):
        return self.is_list() or self.is_set() or self.is_dict() or self.is_tuple()

    def is_str(self):
        return self.is_python_obj("builtins.str")

    def is_int(self):
        return self.__type == LangType.Type.INTEGER

    def is_dec(self):
        return self.__type == LangType.Type.DECIMAL

    def is_bool(self):
        return self.__type == LangType.Type.BOOLEAN

    def is_primitive(self):
        return self.is_int() or self.is_dec() or self.is_bool()

    def is_obj(self):
        return self.__type == LangType.Type.OBJECT

    def is_module(self):
        return self.__type == LangType.Type.MODULE

    def is_python_obj(self, type_path: str = None):
        if type_path is None:
            return self.__type == LangType.Type.PYTHON
        else:
            return self.is_python_obj_of_type(type_path)

    def is_none(self):
        return self.__type == LangType.Type.NONE

    def get_id(self):
        return self.__id

    def get_type(self):
        return self.__type

    def to_code_type(self, code_gen: code_gen.CodeGen):
        result = CodeType()
        if self.is_list() or self.is_dict() or self.is_tuple() or self.is_set():
            result = code_type.get_py_obj_ptr(code_gen)
        elif self.is_int() or self.is_module():
            result = code_type.get_int64()
        elif self.is_dec():
            result = code_type.get_double()
        elif self.is_bool():
            result = code_type.get_int1()
        elif self.is_obj():
            result = code_gen.get_data().get_class(self.__id).get_struct().to_code_type().get_ptr_to()
        elif self.is_python_obj():
            result = code_type.get_py_obj_ptr(code_gen)
        elif self.is_none():
            result = code_type.get_int32()
        elif self.is_unknown():
            result = code_type.get_void()
        return result

    def get_content(self):
        result: list[LangType] = []
        if self.is_collection():  # Let's look at the content of the collection to find content type
            for current_hint in self.__hints:
                if isinstance(current_hint, hint.TypeHintCollectionContentHint):
                    result.append(current_hint.get_hint_type())

        if len(result) == 1:
            return result[0]
        elif len(result) > 1:
            type_result = get_python_obj_type()
            return type_result
        else:
            return get_python_obj_type()

    def is_python_obj_of_type(self, type_path: str):
        for e in self.__hints:
            if isinstance(e, hint.TypeHintPythonType) and e.get_class_path() == type_path:
                return True
        return False

    def add_hint(self, new_hint: hint.TypeHint):
        if isinstance(new_hint, hint.TypeHint):
            self.__hints.append(new_hint)
        else:
            raise ValueError(str(type(new_hint)) + " instead of HintType")

    def remove_hint(self, index: int):
        self.__hints.pop(index)

    def get_hint(self, index: int | PyType[hint.TypeHint]):
        if isinstance(index, int):
            return self.__hints[index]
        result: list[hint.TypeHint | hint.TypeHintPythonType] = []
        for hint in self.__hints:
            if isinstance(hint, index):
                result.append(hint)
        return result

    def get_hints(self):
        return copy.copy(self.__hints)

    def iter_hints(self):
        return iter(self.__hints)

    def clear_hints(self):
        self.__hints.clear()

    def __eq__(self, other: LangType):
        return self.__type == other.__type

    def to_str(self, comp_data: CompData):
        to_str: str
        if self.is_primitive() or self.is_module() or self.is_unknown():
            to_str = str(self)
        elif self.is_none():
            to_str = "None type"
        elif self.is_obj():
            to_str = comp_data.get_class(self.__id).get_name()
        elif self.is_str():
            to_str = "str"
        elif self.is_dict():
            to_str = "dict"
        elif self.is_list():
            to_str = "list"
        elif self.is_set():
            to_str = "set"
        elif self.is_tuple():
            to_str = "tuple"
        elif self.is_python_obj():
            to_str = "Python object"
        else:
            to_str = "Flyable type"
        return to_str

    def __repr__(self):
        str_types = {
            LangType.Type.UNKNOWN: "Unknown",
            LangType.Type.INTEGER: "int",
            LangType.Type.DECIMAL: "float",
            LangType.Type.BOOLEAN: "Bool",
            LangType.Type.OBJECT: "object",
            LangType.Type.MODULE: "module",
            LangType.Type.PYTHON: "python",
            LangType.Type.NONE: "none"
        }

        result = str_types[self.__type]

        if self.is_dict():
            result = "{ " + str(result) + " }"
        elif self.is_list():
            result = "[ " + str(result) + " ]"
        elif self.is_tuple():
            result = "( " + str(result) + " )"

        if len(self.__hints):
            result += "@hints"
            for e in self.__hints:
                result += " " + str(e) + " "

        return result

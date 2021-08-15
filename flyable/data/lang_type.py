import copy
from enum import Enum
from flyable.code_gen.code_type import CodeType
import flyable.code_gen.code_type as code_type


def to_code_type(code_gen, type):
    """
    Convert a list of LangType to a list of CodeType
    Or
    Convert a single LangType to a CodeType
    """
    if isinstance(type, list):
        result = []
        for e in type:
            result.append(e.to_code_type(code_gen))
        return result

    return type.to_code_type(code_gen)


def get_type_common(data, primary_type, second_type=None):
    """
    Return a type that can contains both types.
    Return none if no common types found
    """
    if isinstance(primary_type, list) and second_type is None:
        current_type = primary_type[0]
        type_iter = next(iter(primary_type))
        for e in type_iter:
            current_type = get_type_common(data, current_type, e)
        return current_type
    else:
        if primary_type == second_type:
            return primary_type
        elif primary_type.is_python_obj() or second_type.is_python_obj():
            return get_python_obj_type()
        elif primary_type.is_obj() and second_type.is_obj():
            return get_python_obj_type()
        elif primary_type.is_none() or second_type.is_none():
            return get_python_obj_type()
        elif primary_type.is_primitive() or second_type.is_primitive():
            # If one of them is primitive but they are not equals, only a py object can represent both
            return get_python_obj_type()
        else:
            raise NotImplementedError()


def get_int_type():
    return LangType(LangType.Type.INTEGER)


def get_dec_type():
    return LangType(LangType.Type.DECIMAL)


def get_bool_type():
    return LangType(LangType.Type.BOOLEAN)


def get_python_obj_type():
    return LangType(LangType.Type.PYTHON)


def get_obj_type(id):
    return LangType(LangType.Type.OBJECT, id)


def get_module_type():
    return LangType(LangType.Type.MODULE)


def get_none_type():
    return LangType(LangType.Type.NONE)


def get_list_of_python_obj_type():
    result = LangType(LangType.Type.PYTHON)
    result.add_dim(LangType.Dimension.LIST)
    return result


def get_set_of_python_obj_type():
    result = LangType(LangType.Type.PYTHON)
    result.add_dim(LangType.Dimension.SET)
    return result


def get_unknown_type():
    return LangType(LangType.Type.UNKNOWN)


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
        NONE = 8

    class Dimension(Enum):
        LIST = 0,
        DICT = 1,
        TUPLE = 2,
        SET = 3

    def __init__(self, type=Type.UNKNOWN, id=0):
        if not isinstance(id, int): raise TypeError("Integer expected for id")

        self.__type = type
        self.__id = id
        self.__dims = []
        self.__hints = []  # Hints are extra data that allows the compiler to perform more severe optimization
        self.__can_none = False

    def is_unknown(self):
        return self.__type == LangType.Type.UNKNOWN

    def is_list(self):
        return len(self.__dims) > 0 and self.__dims[-1] == LangType.Dimension.LIST

    def is_dict(self):
        return len(self.__dims) > 0 and self.__dims[-1] == LangType.Dimension.DICT

    def is_set(self):
        return len(self.__dims) > 0 and self.__dims[-1] == LangType.Dimension.SET

    def is_tuple(self):
        return len(self.__dims) > 0 and self.__dims[-1] == LangType.Dimension.TUPLE

    def is_collection(self):
        return self.is_list() or self.is_set() or self.is_dict() or self.is_tuple()

    def is_int(self):
        return len(self.__dims) == 0 and self.__type == LangType.Type.INTEGER

    def is_dec(self):
        return len(self.__dims) == 0 and self.__type == LangType.Type.DECIMAL

    def is_bool(self):
        return self.__type == LangType.Type.BOOLEAN

    def is_primitive(self):
        return self.is_int() or self.is_dec() or self.is_bool()

    def is_obj(self):
        return len(self.__dims) == 0 and self.__type == LangType.Type.OBJECT

    def is_module(self):
        return len(self.__dims) == 0 and self.__type == LangType.Type.MODULE

    def is_python_obj(self):
        return len(self.__dims) == 0 and self.__type == LangType.Type.PYTHON

    def is_none(self):
        return len(self.__dims) == 0 and self.__type == LangType.Type.NONE

    def get_id(self):
        return self.__id

    def can_be_none(self):
        return self.__can_none

    def set_can_be_none(self, can):
        self.__can_none = can

    def to_code_type(self, code_gen):
        result = CodeType()
        if self.is_list() or self.is_dict() or self.is_tuple() or self.is_set():
            result = code_type.get_py_obj_ptr(code_gen)
        elif self.is_int() or self.is_module():
            result = code_type.get_int64()
        elif self.is_dec():
            result = code_type.get_double()
        elif self.is_bool():
            result = code_type.get_int1()
        elif self.is_python_obj():
            result = code_type.get_py_obj_ptr(code_gen)
        elif self.is_obj():
            result = code_gen.get_data().get_class(self.__id).get_struct().to_code_type().get_ptr_to()
        elif self.is_none():
            result = code_type.get_int32()
        elif self.is_unknown():
            result = code_type.get_void()
        return result

    def add_dim(self, dim):
        self.__dims.append(dim)

    def get_dim(self):
        return self.__dims[-1]

    def get_content(self):
        result = copy.copy(self)

        if len(result.__dims) > 0:
            result.__dims.pop()
            if result.is_primitive():
                result.__type = LangType.Type.PYTHON  # A container can only contain python object object
            return result
        return get_python_obj_type()

    def add_hint(self, hint):
        self.__hints.append(hint)

    def remove_hint(self, index):
        self.__hints.pop(index)

    def get_hint(self, index):
        if isinstance(index, int):
            return self.__hints[index]
        else:
            result = []
            for hint in self.__hints:
                if isinstance(hint, index):
                    result.append(hint)
            return result

    def get_hints(self):
        return copy.copy(self.__hints)

    def __eq__(self, other):
        return self.__type == other.__type

    def to_str(self, comp_data):
        if self.is_primitive() or self.is_module() or self.is_unknown():
            return str(self)
        elif self.is_none():
            return "None type"
        elif self.is_obj():
            return comp_data.get_class(self.__id).get_name()
        elif self.is_python_obj():
            return "Python object"
        elif self.is_dict():
            return "dict"
        elif self.is_list():
            return "list"
        elif self.is_set():
            return "set"
        elif self.is_tuple():
            return tuple
        return "Flyable type"

    def __str__(self):
        result = ""

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

        result += str_types[self.__type]

        for dim in self.__dims:
            if dim == LangType.Dimension.DICT:
                result = "{ " + result + " }"
            elif dim == LangType.Dimension.LIST:
                result = "[ " + result + " ]"
            elif dim == LangType.Dimension.TUPLE:
                result = "( " + result + " )"

        return result

from enum import Enum
from flyable.code_gen.code_type import CodeType


def to_code_type(comp_data, type):
    """
    Convert a list of LangType to a list of CodeType
    Or
    Convert a single LangType to a CodeType
    """
    if isinstance(type, list):
        result = []
        for e in type:
            result.append(e.to_code_type(comp_data))
        return result

    return type.to_code_type(comp_data)


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
        BOOLEAN = 7  # Boolean value

    def __init__(self, type=Type.UNKNOWN, id=0):
        if not isinstance(id, int): raise TypeError("Integer expected for id")

        self.__type = type
        self.__id = id
        self.__dims = []
        self.__details = [] # Details are extra data that allows the compiler to perform more severe optimization

    def is_unknown(self):
        return self.__type == LangType.Type.UNKNOWN

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

    def to_code_type(self, comp_data):
        result = CodeType()
        if self.is_int() or self.is_module():
            result = CodeType(CodeType.CodePrimitive.INT64)
        elif self.is_dec():
            result = CodeType(CodeType.CodePrimitive.DOUBLE)
        elif self.is_bool():
            result = CodeType(CodeType.CodePrimitive.INT1)
        elif self.is_python_obj():
            result = CodeType(CodeType.CodePrimitive.STRUCT)
        elif self.is_obj():
            result = comp_data.get_class(self.__id).get_struct().to_code_type().get_ptr_to()

        return result

    def __eq__(self, other):
        return self.__type == other.__type

    def to_str(self, comp_data):
        if self.is_primitive() or self.is_module() or self.is_unknown():
            return str(self)
        elif self.is_obj():
            return comp_data.get_class(self.__id).get_name()
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

        }

        result += str_types[self.__type]
        return result

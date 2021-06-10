import enum


def get_void():
    return CodeType(CodeType.CodePrimitive.VOID)


def get_int64():
    return CodeType(CodeType.CodePrimitive.INT64)


def get_int32():
    return CodeType(CodeType.CodePrimitive.INT32)


def get_int16():
    return CodeType(CodeType.CodePrimitive.INT16)


def get_int8():
    return CodeType(CodeType.CodePrimitive.INT8)


def get_int8_ptr():
    return get_int8().get_ptr_to()


class CodeType:
    """
    CodeType represents a type that can be describe in low-level machine code.
    It can also refer to a native data structure.
    """

    class CodePrimitive(enum.IntEnum):
        INT1 = 0,
        INT8 = 1,
        INT16 = 2,
        INT32 = 3,
        INT64 = 4,
        FLOAT = 5,
        DOUBLE = 6,
        VOID = 7,
        STRUCT = 8,

    def __init__(self, type=CodePrimitive.VOID, id=0):
        self.__type = type
        self.__ptr_level = 0
        self.__struct_id = id

    def get_ptr_to(self):
        result = CodeType()
        result.__type = self.__type
        result.__ptr_level = self.__ptr_level
        result.__struct_id = self.__struct_id
        result.__ptr_level += 1
        return result

    def get_struct_id(self):
        return self.__struct_id

    def get_ptr_level(self):
        return self.__ptr_level

    def get_null_value(self, builder):
        if self.__ptr_level == 0:
            if self.__type == CodeType.CodePrimitive.INT64:
                return builder

    def write_to_code(self, writer):
        writer.add_int32(int(self.__type))
        writer.add_int32(int(self.__ptr_level))
        writer.add_int32(int(self.__struct_id))

    def __eq__(self, other):
        return self.__type == other.__type \
               and self.__struct_id == other.__struct_id \
               and self.__ptr_level == other.__ptr_level

    def __str__(self):
        str_types = {
            CodeType.CodePrimitive.VOID: "void",
            CodeType.CodePrimitive.INT64: "int64",
            CodeType.CodePrimitive.INT8: "int8",
            CodeType.CodePrimitive.INT16: "int16",
            CodeType.CodePrimitive.INT32: "int32",
            CodeType.CodePrimitive.FLOAT: "float",
            CodeType.CodePrimitive.DOUBLE: "double",
            CodeType.CodePrimitive.STRUCT: "struct"
        }

        result = str_types[self.__type]
        for e in range(self.__ptr_level):
            result += "*"

        return result


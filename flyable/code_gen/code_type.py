import enum
import copy


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


def get_int1():
    return CodeType(CodeType.CodePrimitive.INT1)


def get_int8_ptr():
    return get_int8().get_ptr_to()


def get_py_obj(code_gen):
    return CodeType(CodeType.CodePrimitive.STRUCT, code_gen.get_py_obj_struct().get_id())


def get_py_obj_ptr(code_gen):
    return get_py_obj(code_gen).get_ptr_to()


def get_py_type(code_gen):
    return CodeType(CodeType.CodePrimitive.STRUCT, code_gen.get_python_type().get_id())


def get_list_obj(code_gen):
    return CodeType(CodeType.CodePrimitive.STRUCT, code_gen.get_py_list_struct().get_id())


def get_list_obj_ptr(code_gen):
    return get_list_obj(code_gen).get_ptr_to()


def get_float():
    return CodeType(CodeType.CodePrimitive.FLOAT)


def get_double():
    return CodeType(CodeType.CodePrimitive.DOUBLE)


def get_func(return_type, args):
    result = CodeType(CodeType.CodePrimitive.FUNC)
    result.set_func_return_type(return_type)
    result.set_func_args(args)
    return result


def get_array_of(type, size):
    result = CodeType(CodeType.CodePrimitive.ARRAY)
    result.set_array_type(type)
    result.set_array_size(size)
    return result


def get_vector_call_func(code_gen):
    args = [get_py_obj_ptr(code_gen), get_py_obj_ptr(code_gen).get_ptr_to(), get_int64(), get_py_obj_ptr(code_gen)]
    return get_func(get_py_obj_ptr(code_gen), args)


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
        FUNC = 9,
        ARRAY = 10

    def __init__(self, type=CodePrimitive.VOID, id=0):
        self.__type = type
        self.__ptr_level = 0
        self.__struct_id = id
        self.__func_args = []
        self.__func_return_type = None
        self.__array_type = None
        self.__array_size = 0

    def get_ptr_to(self):
        result = copy.copy(self)
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

    def set_func_args(self, args):
        self.__func_args = args

    def set_func_return_type(self, return_type):
        self.__func_return_type = return_type

    def set_array_type(self, array_type):
        self.__array_type = array_type

    def set_array_size(self, size):
        self.__array_size = size

    def write_to_code(self, writer):
        writer.add_int32(int(self.__type))
        writer.add_int32(int(self.__ptr_level))
        writer.add_int32(int(self.__struct_id))

        if self.__type == CodeType.CodePrimitive.FUNC:
            self.__func_return_type.write_to_code(writer)
            writer.add_int32(len(self.__func_args))
            for arg in self.__func_args:
                arg.write_to_code(writer)
        elif self.__type == CodeType.CodePrimitive.ARRAY:
            self.__array_type.write_to_code(writer)
            writer.add_int32(self.__array_size)

    def __eq__(self, other):
        return self.__type == other.__type \
               and self.__struct_id == other.__struct_id \
               and self.__ptr_level == other.__ptr_level

    def __str__(self):
        str_types = {
            CodeType.CodePrimitive.VOID: "void",
            CodeType.CodePrimitive.INT64: "int64",
            CodeType.CodePrimitive.INT8: "int8",
            CodeType.CodePrimitive.INT1: "int1",
            CodeType.CodePrimitive.INT16: "int16",
            CodeType.CodePrimitive.INT32: "int32",
            CodeType.CodePrimitive.FLOAT: "float",
            CodeType.CodePrimitive.DOUBLE: "double",
            CodeType.CodePrimitive.STRUCT: "struct( " + str(self.__struct_id) + " )",
            CodeType.CodePrimitive.FUNC: "func",
            CodeType.CodePrimitive.ARRAY: "array[" + str(self.__array_size) + " x " + str(self.__array_type) + "]"
        }

        result = str_types[self.__type]
        for e in range(self.__ptr_level):
            result += "*"

        return result

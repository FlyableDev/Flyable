from typing import Any
import flyable.code_gen.code_gen as gen


class CodeBuilder:
    """
    CodeBuilder writes the data that will be passed to generate binary to send to the code generation native layer.
    It mimics the LLVM IRBuilder API but with some extra type abstractions.
    """

    def __init__(self, func):
        self.__current_block = None
        self.__func = func
        self.__writer = None

    def to_bytes(self):
        return self.__writer.to_bytes()

    def create_block(self):
        return self.__gen_block()

    def set_insert_block(self, block):
        self.__writer = block.get_writer()
        self.__current_block = block

    def get_current_block(self):
        return self.__current_block

    def add(self, v1, v2):
        return self.__make_op(1, v1, v2)

    def sub(self, v1, v2):
        return self.__make_op(2, v1, v2)

    def mul(self, v1, v2):
        return self.__make_op(3, v1, v2)

    def div(self, v1, v2):
        return self.__make_op(4, v1, v2)

    def eq(self, v1, v2):
        return self.__make_op(5, v1, v2)

    def ne(self, v1, v2):
        return self.__make_op(6, v1, v2)

    def lt(self, v1, v2):
        return self.__make_op(7, v1, v2)

    def lte(self, v1, v2):
        return self.__make_op(8, v1, v2)

    def gt(self, v1, v2):
        return self.__make_op(9, v1, v2)

    def gte(self, v1, v2):
        return self.__make_op(10, v1, v2)

    def neg(self, value):
        return self.__make_op(11, value)

    def _and(self, v1, v2):
        return self.__make_op(12, v1, v2)

    def _or(self, v1, v2):
        return self.__make_op(13, v1, v2)

    def mod(self, v1, v2):
        return self.__make_op(14, v1, v2)

    def _not(self, value):
        return self.__make_op(15, value)

    def store(self, value, store):
        return self.__make_op(100, value, store)

    def load(self, value):
        return self.__make_op(101, value)

    def br(self, block):
        self.__writer.add_int32(150)
        self.__writer.add_int32(block.get_id())
        self.__current_block.add_br_block(block)
        self.__writer.lock()

    def cond_br(self, value, block_true, block_false):
        self.__writer.add_int32(151)
        self.__writer.add_int32(value)
        self.__writer.add_int32(block_true.get_id())
        self.__writer.add_int32(block_false.get_id())
        self.__current_block.add_br_block(block_true)
        self.__current_block.add_br_block(block_false)
        self.__writer.lock()

    def gep(self, value, first_index, second_index):
        return self.__make_op(152, value, first_index, second_index)

    def gep2(self, value, type, array_indices):
        self.__writer.add_int32(153)
        type.write_to_code(self.__writer)
        self.__writer.add_int32(value)
        self.__writer.add_int32(len(array_indices))
        for index in array_indices:
            self.__writer.add_int32(index)
        return self.__gen_value()

    def call(self, func, args):
        return self.__make_op(170, func.get_id(), len(args), *args)

    def call_ptr(self, ptr, args, call_conv=None):
        return self.__make_op(171, ptr, call_conv if call_conv is not None else gen.CallingConv.C, len(args), *args)

    def const_int64(self, value):
        self.__writer.add_int32(1000)
        self.__writer.add_int64(value)
        return self.__gen_value()

    def const_int32(self, value):
        return self.__make_op(1001, value)

    def const_int16(self, value):
        return self.__make_op(1002, value)

    def const_int8(self, value):
        return self.__make_op(1003, value)

    def const_int1(self, value):
        return self.__make_op(1007, int(value))

    def const_float32(self, value):
        self.__writer.add_float32(1004)
        self.__writer.add_float32(value)
        return self.__gen_value()

    def const_float64(self, value):
        self.__writer.add_int32(1005)
        self.__writer.add_float64(value)
        return self.__gen_value()

    def const_null(self, type):
        self.__writer.add_int32(1006)
        type.write_to_code(self.__writer)
        return self.__gen_value()

    def ptr_cast(self, value, type):
        self.__writer.add_int32(1010)
        self.__writer.add_int32(value)
        type.write_to_code(self.__writer)
        return self.__gen_value()

    def int_cast(self, value, type):
        self.__writer.add_int32(1011)
        self.__writer.add_int32(value)
        type.write_to_code(self.__writer)
        return self.__gen_value()

    def float_cast(self, value, type):
        self.__writer.add_int32(1012)
        self.__writer.add_int32(value)
        type.write_to_code(self.__writer)
        return self.__gen_value()

    def int_to_ptr(self, value, ptr_type):
        self.__writer.add_int32(1013)
        self.__writer.add_int32(value)
        ptr_type.write_to_code(self.__writer)
        return self.__gen_value()

    def bit_cast(self, value, cast_type):
        self.__writer.add_int32(1014)
        self.__writer.add_int32(value)
        cast_type.write_to_code(self.__writer)
        return self.__gen_value()

    def zext(self, value, cast_type):
        self.__writer.add_int32(1015)
        self.__writer.add_int32(value)
        cast_type.write_to_code(self.__writer)
        return self.__gen_value()

    def alloca(self, type):
        self.__writer.add_int32(1050)
        type.write_to_code(self.__writer)
        return self.__gen_value()

    def ret(self, value):
        self.__writer.add_int32(2000)
        self.__writer.add_int32(value)
        self.__current_block.set_has_return(True)
        self.__writer.lock()

    def ret_void(self):
        self.__writer.add_int32(2001)
        self.__current_block.set_has_return(True)
        self.__writer.lock()

    def ret_null(self):
        self.__writer.add_int32(2002)
        self.__current_block.set_has_return(True)
        self.__writer.lock()

    def global_var(self, var):
        return self.__make_op(3000, var.get_id())

    def global_str(self, value):
        self.__writer.add_int32(3001)
        self.__writer.add_str(value)
        return self.__gen_value()

    def size_of_type(self, type):
        self.__writer.add_int32(9998)
        type.write_to_code(self.__writer)
        return self.__gen_value()

    def size_of_type_ptr_element(self, type):
        self.__writer.add_int32(9999)
        type.write_to_code(self.__writer)
        return self.__gen_value()

    def print_value_type(self, value):
        self.__writer.add_int32(10000)
        self.__writer.add_int32(value)

    def get_total_value(self):
        return self.__current_id

    def get_total_block(self):
        return self.__current_block

    def get_writer(self):
        return self.__writer

    def __gen_value(self):
        new_value = self.__func.increment_value()
        self.__writer.add_int32(new_value)
        return new_value

    def __gen_block(self):
        result = self.__func.add_block()
        return result

    def __make_op(self, id: int, *values: Any) -> Any:
        """
        This function adds, to the writer, the id and each subsequent values passed in the parameter
        values. 
        Then, it calls self.__gen_value() and returns its result

        Args:
            id (int): the id of the operation

        Returns:
            Any: the result of self.__gen_value()
        """
        self.__writer.add_int32(id)
        for v in values:
            self.__writer.add_int32(v)
        return self.__gen_value()

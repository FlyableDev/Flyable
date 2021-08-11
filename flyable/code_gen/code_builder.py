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
        self.__writer.add_int32(1)
        self.__writer.add_int32(v1)
        self.__writer.add_int32(v2)
        return self.__gen_value()

    def sub(self, v1, v2):
        self.__writer.add_int32(2)
        self.__writer.add_int32(v1)
        self.__writer.add_int32(v2)
        return self.__gen_value()

    def mul(self, v1, v2):
        self.__writer.add_int32(3)
        self.__writer.add_int32(v1)
        self.__writer.add_int32(v2)
        return self.__gen_value()

    def div(self, v1, v2):
        self.__writer.add_int32(4)
        self.__writer.add_int32(v1)
        self.__writer.add_int32(v2)
        return self.__gen_value()

    def eq(self, v1, v2):
        self.__writer.add_int32(5)
        self.__writer.add_int32(v1)
        self.__writer.add_int32(v2)
        return self.__gen_value()

    def ne(self, v1, v2):
        self.__writer.add_int32(6)
        self.__writer.add_int32(v1)
        self.__writer.add_int32(v2)
        return self.__gen_value()

    def lt(self, v1, v2):
        self.__writer.add_int32(7)
        self.__writer.add_int32(v1)
        self.__writer.add_int32(v2)
        return self.__gen_value()

    def lte(self, v1, v2):
        self.__writer.add_int32(8)
        self.__writer.add_int32(v1)
        self.__writer.add_int32(v2)
        return self.__gen_value()

    def gt(self, v1, v2):
        self.__writer.add_int32(9)
        self.__writer.add_int32(v1)
        self.__writer.add_int32(v2)
        return self.__gen_value()

    def gte(self, v1, v2):
        self.__writer.add_int32(10)
        self.__writer.add_int32(v1)
        self.__writer.add_int32(v2)
        return self.__gen_value()

    def neg(self, value):
        self.__writer.add_int32(11)
        self.__writer.add_int32(value)
        return self.__gen_value()

    def _and(self, v1, v2):
        self.__writer.add_int32(12)
        self.__writer.add_int32(v1)
        self.__writer.add_int32(v2)
        return self.__gen_value()

    def _or(self, v1, v2):
        self.__writer.add_int32(13)
        self.__writer.add_int32(v1)
        self.__writer.add_int32(v2)
        return self.__gen_value()

    def mod(self, v1, v2):
        self.__writer.add_int32(14)
        self.__writer.add_int32(v1)
        self.__writer.add_int32(v2)
        return self.__gen_value()

    def store(self, value, store):
        self.__writer.add_int32(100)
        self.__writer.add_int32(value)
        self.__writer.add_int32(store)
        return self.__gen_value()

    def load(self, value):
        self.__writer.add_int32(101)
        self.__writer.add_int32(value)
        return self.__gen_value()

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
        self.__writer.add_int32(152)
        self.__writer.add_int32(value)
        self.__writer.add_int32(first_index)
        self.__writer.add_int32(second_index)
        return self.__gen_value()

    def gep2(self, value, type, array_indices):
        self.__writer.add_int32(153)
        type.write_to_code(self.__writer)
        self.__writer.add_int32(value)
        self.__writer.add_int32(len(array_indices))
        for index in array_indices:
            self.__writer.add_int32(index)
        return self.__gen_value()

    def call(self, func, args):
        self.__writer.add_int32(170)
        self.__writer.add_int32(func.get_id())
        self.__writer.add_int32(len(args))
        for e in args:
            self.__writer.add_int32(e)
        return self.__gen_value()

    def call_ptr(self, ptr, args, call_conv=None):
        self.__writer.add_int32(171)
        self.__writer.add_int32(ptr)
        if call_conv is None:
            call_conv = gen.CallingConv.C
        self.__writer.add_int32(call_conv)

        self.__writer.add_int32(len(args))
        for e in args:
            self.__writer.add_int32(e)
        return self.__gen_value()

    def const_int64(self, value):
        self.__writer.add_int32(1000)
        self.__writer.add_int64(value)
        return self.__gen_value()

    def const_int32(self, value):
        self.__writer.add_int32(1001)
        self.__writer.add_int32(value)
        return self.__gen_value()

    def const_int16(self, value):
        self.__writer.add_int32(1002)
        self.__writer.add_int32(value)
        return self.__gen_value()

    def const_int8(self, value):
        self.__writer.add_int32(1003)
        self.__writer.add_int32(value)
        return self.__gen_value()

    def const_int1(self, value):
        self.__writer.add_int32(1007)
        self.__writer.add_int32(int(value))
        return self.__gen_value()

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
        self.__writer.add_int32(3000)
        self.__writer.add_int32(var.get_id())
        return self.__gen_value()

    def global_str(self, value):
        self.__writer.add_int32(3001)
        self.__writer.add_str(value)
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

    def __gen_value(self):
        new_value = self.__func.increment_value()
        self.__writer.add_int32(new_value)
        return new_value

    def __gen_block(self):
        result = self.__func.add_block()
        return result

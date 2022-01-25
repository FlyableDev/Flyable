from __future__ import annotations
from typing import TYPE_CHECKING, Any
from flyable.code_gen.code_type import CodeType
from flyable.code_gen.code_writer import CodeWriter
import flyable.debug.debug_flags as debug_flags
import inspect
import flyable.code_gen.code_gen as gen

if TYPE_CHECKING:
    from flyable.code_gen.code_gen import CodeFunc
    from flyable.data.lang_func import LangFunc

class CodeBuilder:
    """
    CodeBuilder writes the data that will be passed to generate binary to send to the code generation native layer.
    It mimics the LLVM IRBuilder API but with some extra type abstractions.
    """

    def __init__(self, func):
        self.__current_block: Any = None
        self.__func: gen.CodeFunc = func
        self.__writer: CodeWriter | None = None

    @property
    def writer(self):
        if self.__writer is None:
            raise Exception("Must first insert a block to get the writer")
        return self.__writer

    def to_bytes(self):
        return self.writer.to_bytes()

    def create_block(self):
        return self.__gen_block()

    def set_insert_block(self, block: CodeFunc.CodeBlock):
        self.__writer = block.get_writer()
        self.__current_block = block

    def get_current_block(self):
        return self.__current_block

    def add(self, v1: int, v2: int):
        """
        Addition
        """
        return self.__make_op(1, v1, v2)

    def sub(self, v1: int, v2: int):
        """
        Substraction
        """
        return self.__make_op(2, v1, v2)

    def mul(self, v1: int, v2: int):
        """
        Multiplication
        """
        return self.__make_op(3, v1, v2)

    def div(self, v1, v2):
        """
        Division
        """
        return self.__make_op(4, v1, v2)

    def eq(self, v1, v2):
        """
        Equality check
        """
        return self.__make_op(5, v1, v2)

    def ne(self, v1, v2):
        """
        Non-Equality check
        """
        return self.__make_op(6, v1, v2)

    def lt(self, v1, v2):
        """
        Less than
        """
        return self.__make_op(7, v1, v2)

    def lte(self, v1, v2):
        """
        Less than or equal
        """
        return self.__make_op(8, v1, v2)

    def gt(self, v1, v2):
        """
        Greater than
        """
        return self.__make_op(9, v1, v2)

    def gte(self, v1, v2):
        """
        Greater than or equal
        """
        return self.__make_op(10, v1, v2)

    def neg(self, value):
        """
        Negation operator
        """
        return self.__make_op(11, value)

    # And operator
    def _and(self, v1, v2):
        return self.__make_op(12, v1, v2)

    def _or(self, v1, v2):
        """
        Or operator
        """
        return self.__make_op(13, v1, v2)

    def mod(self, v1, v2):
        """
        Modulo operator
        """
        return self.__make_op(14, v1, v2)

    def _not(self, value):
        """
        Not operator
        """
        return self.__make_op(15, value)

    def store(self, value: int, store: int):
        """
        Store value in memory
        """
        return self.__make_op(100, value, store)

    def load(self, value: int):
        """
        Load value from memory
        """
        return self.__make_op(101, value)

    def br(self, block: CodeFunc.CodeBlock):
        self.__write_opcode(150)
        self.writer.add_int32(block.get_id())
        self.__current_block.add_br_block(block)
        self.writer.lock()

    def cond_br(self, value: int, block_true: CodeFunc.CodeBlock, block_false: CodeFunc.CodeBlock):
        self.__write_opcode(151)
        self.writer.add_int32(value)
        self.writer.add_int32(block_true.get_id())
        self.writer.add_int32(block_false.get_id())
        self.__current_block.add_br_block(block_true)
        self.__current_block.add_br_block(block_false)
        self.writer.lock()

    def gep(self, value: int, first_index: int, second_index: int):
        return self.__make_op(152, value, first_index, second_index)

    def gep2(self, value: int, type: CodeType, array_indices: list[int]):
        self.__write_opcode(153)
        type.write_to_code(self.writer)
        self.writer.add_int32(value)
        self.writer.add_int32(len(array_indices))
        for index in array_indices:
            self.writer.add_int32(index)
        return self.__gen_value()

    def call(self, func: CodeFunc, args):
        """
        Function call with CodeFunc
        """
        return self.__make_op(170, func.get_id(), len(args), *args)

    def call_ptr(self, ptr: int, args, call_conv:bool=None):
        """
        Function call with pointer
        """
        return self.__make_op(
            171,
            ptr,
            call_conv if call_conv is not None else gen.CallingConv.C,
            len(args),
            *args
        )

    def const_int64(self, value: int):
        """
        Allocate int64 memory location
        """
        self.__write_opcode(1000)
        self.writer.add_int64(value)
        return self.__gen_value()

    def const_int32(self, value: int):
        """
        Allocate int32 memory location
        """
        return self.__make_op(1001, value)

    def const_int16(self, value: int):
        """
        Allocate int16 memory location
        """
        return self.__make_op(1002, value)

    def const_int8(self, value: int):
        """
        Allocate int8 memory location
        """
        return self.__make_op(1003, value)

    def const_int1(self, value: int | bool):
        """
        Allocate int1 memory location
        """
        return self.__make_op(1007, int(value))

    def const_float32(self, value: int):
        """
        Allocate float32 memory location
        """
        self.__write_opcode(1004)
        self.writer.add_float32(value)
        return self.__gen_value()

    def const_float64(self, value: int):
        """
        Allocate float64 memory location
        """
        self.__write_opcode(1005)
        self.writer.add_float64(value)
        return self.__gen_value()

    def const_null(self, type: CodeType):
        """
        Allocate null memory location
        """
        self.__write_opcode(1006)
        type.write_to_code(self.writer)
        return self.__gen_value()

    def ptr_cast(self, value: int, type: CodeType):
        """
        Value to pointer
        """
        self.__write_opcode(1010)
        self.writer.add_int32(value)
        type.write_to_code(self.writer)
        return self.__gen_value()

    def int_cast(self, value: int, type: CodeType):
        """
        Cast int
        """
        self.__write_opcode(1011)
        self.writer.add_int32(value)
        type.write_to_code(self.writer)
        return self.__gen_value()

    def float_cast(self, value: int, type: CodeType):
        """
        Cast float
        """
        self.__write_opcode(1012)
        self.writer.add_int32(value)
        type.write_to_code(self.writer)
        return self.__gen_value()

    def int_to_ptr(self, value: int, ptr_type: CodeType):
        self.__write_opcode(1013)
        self.writer.add_int32(value)
        ptr_type.write_to_code(self.writer)
        return self.__gen_value()

    def bit_cast(self, value, cast_type: CodeType):
        self.__write_opcode(1014)
        self.writer.add_int32(value)
        cast_type.write_to_code(self.writer)
        return self.__gen_value()

    def zext(self, value: int, cast_type: CodeType):
        self.__write_opcode(1015)
        self.writer.add_int32(value)
        cast_type.write_to_code(self.writer)
        return self.__gen_value()

    def alloca(self, type: CodeType):
        self.__write_opcode(1050)
        type.write_to_code(self.writer)
        return self.__gen_value()

    def ret(self, value: int):
        self.__write_opcode(2000)
        self.writer.add_int32(value)
        self.__current_block.set_has_return(True)
        self.writer.lock()

    def ret_void(self):
        self.__write_opcode(2001)
        self.__current_block.set_has_return(True)
        self.writer.lock()

    def ret_null(self):
        self.__write_opcode(2002)
        self.__current_block.set_has_return(True)
        self.writer.lock()

    def global_var(self, var: gen.GlobalVar):
        return self.__make_op(3000, var.get_id())

    def global_str(self, value: str):
        self.__write_opcode(3001)
        self.writer.add_str(value)
        return self.__gen_value()

    def func_ptr(self, func: LangFunc):
        return self.__make_op(3002, func.get_id())

    def size_of_type(self, type: CodeType):
        self.__write_opcode(9998)
        type.write_to_code(self.writer)
        return self.__gen_value()

    def size_of_type_ptr_element(self, type: CodeType):
        self.__write_opcode(9999)
        type.write_to_code(self.writer)
        return self.__gen_value()

    def print_value_type(self, value: int):
        self.__write_opcode(10000)
        self.writer.add_int32(value)

    def debug_op(self):
        self.__write_opcode(10001)

    def debug_op2(self):
        self.__write_opcode(10002)

    def get_total_value(self):
        return self.__current_id

    def get_total_block(self):
        return self.__current_block

    def get_writer(self):
        return self.writer

    def __gen_value(self):
        new_value = self.__func.increment_value()
        self.writer.add_int32(new_value)
        return new_value

    def __gen_block(self):
        result = self.__func.add_block()
        return result

    def __make_op(self, id: int, *values: int) -> int:
        """
        This function adds, to the writer, the id and each subsequent values passed in the parameter
        values.
        Then, it calls self.__gen_value() and returns its result

        Args:
            id (int): the id of the operation

        Returns:
            Any: the result of self.__gen_value()
        """
        self.__write_opcode(id)
        for v in values:
            self.writer.add_int32(v)
        return self.__gen_value()

    def __write_opcode(self, opcode: int):
        if debug_flags.DebugFlags.SHOW_OPCODE_ON_EXEC.is_enabled:
            stack_str = ""
            for stack_info in inspect.stack():
                file = stack_info.filename
                line = stack_info.lineno
                func_name = stack_info.function
                stack_str += file + " / " + func_name + " / " + str(line)
                stack_str += "\n"
            self.writer.add_str(stack_str)
        self.writer.add_int32(opcode)

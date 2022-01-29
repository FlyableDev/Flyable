"""
Module containing all the different initializer for global variable
"""
from flyable.code_gen.code_writer import CodeWriter

class ConstInitializer:

    def write_to_code(self, writer: CodeWriter):
        writer.add_int32(0)

class StringConstInitializer(ConstInitializer):

    def __init__(self, value: str):
        self.__value = value

    def write_to_code(self, writer: CodeWriter):
        writer.add_int32(1)
        writer.add_str(self.__value)


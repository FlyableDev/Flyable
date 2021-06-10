"""
Module containing all the different initializer for global variable
"""


class ConstInitializer:

    def write_to_code(self, writer):
        pass

class StringConstInitializer(ConstInitializer):

    def __init__(self, value):
        self.__value = value

    def write_to_code(self, writer):
        writer.add_int32(1)
        writer.add_str(self.__value)


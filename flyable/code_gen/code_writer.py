import struct


class CodeWriter:
    """
    This class holds all the methods to binary write data.
    """

    def __init__(self):
        self.__lock = False  # To allow a block any writing on the data
        self.__data = bytearray()

    def to_bytes(self):
        return self.__data.to_bytes()

    def add_int32(self, value):
        if not self.is_lock():
            self.__data += value.to_bytes(4, byteorder='little', signed=True)

    def add_int64(self, value):
        if not self.is_lock():
            self.__data += value.to_bytes(8, byteorder='little', signed=True)

    def add_float32(self, value):
        if not self.is_lock():
            bytes = bytearray(struct.pack("f", value))
            self.__data += bytes

    def add_float64(self, value):
        if not self.is_lock():
            bytes = bytearray(struct.pack("d", value))
            self.__data += bytes

    def add_str(self, value: str):
        if not self.is_lock():
            self.add_int32(len(value))
            self.__data += str.encode(value)

    def add_bytes(self, bytes):
        if not self.is_lock():
            self.__data += bytes

    def write_to_code(self, writer):
        writer.add_int32(len(self.__data))
        writer.add_bytes(self.__data)

    def get_data(self):
        return self.__data

    def lock(self):
        self.__lock = True

    def is_lock(self):
        return self.__lock

    def __len__(self):
        return len(self.__data)

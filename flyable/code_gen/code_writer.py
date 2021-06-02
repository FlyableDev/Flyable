class CodeWriter:
    '''
    This class holds all the methods to binary write data.
    '''

    def __init__(self):
        self.__data = bytearray()

    def to_bytes(self):
        return self.__data.to_bytes()

    def add_int32(self, value):
        self.__data += value.to_bytes(4, byteorder='little', signed=True)

    def add_int64(self, value):
        self.__data += value.to_bytes(8, byteorder='little', signed=True)

    def add_float32(self, value):
        self.__data += value.to_bytes(4, byteorder='little')

    def add_float64(self, value):
        self.__data += value.to_bytes(8, byteorder='little')

    def add_str(self, value):
        self.add_int32(len(value))
        self.__data += str.encode(value)

    def add_bytes(self, bytes):
        self.__data += bytes

    def write_to_code(self, writer):
        writer.add_int32(len(self.__data))
        writer.add_bytes(self.__data)

    def get_data(self):
        return self.__data

    def __len__(self):
        return len(self.__data)

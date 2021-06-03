import os
import sys

"""
Module related to the dynamic loading of the native code generation layer
"""

import ctypes as ctypes


def __load_lib():
    path = dir_path = os.path.dirname(os.path.realpath(__file__)) + "\\..\\dyn_lib\\win64"
    os.add_dll_directory(path)
    return ctypes.CDLL("FlyableCodeGen.dll")


def call_code_generation_layer(writer, output):
    lib = __load_lib()
    gen_func = lib.flyable_codegen_run
    buffer_size = len(writer)
    native_buffer = (ctypes.c_char * buffer_size).from_buffer(writer.get_data())
    output_c_str = ctypes.c_char_p(output.encode("utf-8"))
    gen_func(native_buffer, ctypes.c_int32(buffer_size), output_c_str)

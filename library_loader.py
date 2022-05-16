import os
import platform

"""
Module related to the dynamic loading of the native code generation layer
"""

import ctypes as ctypes
import atexit
import inspect

__lib = None


def __load_lib():
    path = os.path.dirname(os.path.realpath(__file__))
    lib_path = ""
    if platform.uname()[0] == "Windows":
        path += ".\\dyn_lib\\win64"
        lib_path = "FlyableJIT.dll"
        os.add_dll_directory(path)
        return ctypes.CDLL(lib_path)
    elif platform.uname()[0] == "Linux":
        lib_name = "FlyableJIT.so"
        path += "./dyn_lib/linux64/"
        lib_path = path
        return load_lib_and_dependecies(lib_path, lib_name)
    elif platform.system() == "Darwin" and platform.machine() == "arm64":
        lib_name = "FlyableJIT.dylib"
        path += "./dyn_lib/macos-arm64/"
        lib_path = path
        return load_lib_and_dependecies(lib_path, lib_name)
    else:
        raise OSError("OS not supported")


def call():
    global __lib
    func_to_get_source = inspect.getsource
    lib = __load_lib()
    gen_func = lib.flyable_run
    gen_func(ctypes.py_object(func_to_get_source))


def load_lib_and_dependecies(path: str, lib: str):
    try:
        return ctypes.CDLL(path + lib)
    except OSError as excp:
        # Get the name of the library not found
        error_msg: str = excp.args[0]
        # Should crash for any errors that are not missing object file
        # errors, since we can't handle them
        if not "cannot open shared" in error_msg:
            # https://stackoverflow.com/questions/24752395/python-raise-from-usage
            # Helps to avoid a massive error message due to recursive calls
            raise excp from None
        lib_load = error_msg.split(" ")[0]
        lib_load = lib_load[0:-1]
        # Now load it
        load_lib_and_dependecies(path, lib_load)
    # Make sure to still return a value if we handled an exception
    return load_lib_and_dependecies(path, lib)
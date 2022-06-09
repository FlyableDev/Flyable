
import platform
import os
import ctypes as ctypes
import inspect
import importlib.resources
from flyable.utils import get_lib_folder_name, get_extension
from flyable import get_package_data_path


"""
Module related to the dynamic loading of the native code generation layer
"""


__lib = None


def __load_lib():
    if (
        platform.system() == "Windows"
        or platform.system() == "Linux"
        or (platform.system() == "Darwin" and platform.machine() == "arm64")
    ):
        return load_lib_and_dependecies(f"libflyableengine.{get_extension()}")
    else:
        raise OSError(f"OS not supported {platform.system()}--{platform.machine()}")


def call():
    global __lib
    func_to_get_source = inspect.getsource
    lib = __load_lib()
    gen_func = lib.flyable_run
    gen_func(ctypes.py_object(func_to_get_source))


def load_lib_and_dependecies(lib_name: str):
    try:
        with importlib.resources.path(
            f"flyable.dyn_lib.{get_lib_folder_name()}", f"{lib_name}"
        ) as lib:
            dll_path = get_package_data_path(get_lib_folder_name())
            return ctypes.CDLL(os.path.join(dll_path, lib.name))
    except OSError as excp:
        # Get the name of the library not found
        error_msg: str = excp.args[0]
        # Should crash for any errors that are not missing object file
        # errors, since we can't handle them
        if not "cannot open shared" in error_msg:
            # https://stackoverflow.com/questions/24752395/python-raise-from-usage
            # Helps to avoid a massive error message due to recursive calls
            raise excp from None
        end_sep = error_msg.find(f".{get_extension()}")
        lib_to_load = f"{error_msg[0:end_sep]}.{get_extension()}"
        #Now load it
        load_lib_and_dependecies(lib_to_load)
    # Make sure to still return a value if we handled an exception
    return load_lib_and_dependecies(lib_name)

import os
import pathlib
import platform

ROOT_DIRECTORY = pathlib.Path(__file__).absolute().parent.parent
RESOURCES_DIRECTORY = os.path.join(ROOT_DIRECTORY, "resources")
BUILD_FILES_DIRECTORY = os.path.join(RESOURCES_DIRECTORY, "build_files")

LIB_FLYABLE_RUNTIME_PATH = os.path.join(BUILD_FILES_DIRECTORY, "libFlyableRuntime.a")
PYTHON_3_11 = "python311.lib" if platform.system() == "Windows" else "python3.11.a" if platform.system() == "Linux" else "libpython3.11d.a"
PYTHON_3_11_PATH = os.path.join(BUILD_FILES_DIRECTORY, PYTHON_3_11)
PYTHON_3_11_DLL_PATH = os.path.join(BUILD_FILES_DIRECTORY, "python311.dll")

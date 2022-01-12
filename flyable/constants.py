import os
import pathlib
import platform

ROOT_DIRECTORY = pathlib.Path(__file__).absolute().parent.parent
RESOURCES_DIRECTORY = os.path.join(ROOT_DIRECTORY, "resources")
BUILD_FILES_DIRECTORY = os.path.join(RESOURCES_DIRECTORY, "build_files")

LIB_FLYABLE_RUNTIME_PATH = os.path.join(BUILD_FILES_DIRECTORY, "libFlyableRuntime.a")
PYTHON_3_10 = "python310.lib" if platform.system() == "Windows" else "python3.10.a" if platform.system() == "Linux" else "python310.dylib"
PYTHON_3_10_PATH = os.path.join(BUILD_FILES_DIRECTORY, PYTHON_3_10)

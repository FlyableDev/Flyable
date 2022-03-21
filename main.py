"""
Here is an example on how to use Flyable.
You need to have the GCC compiler in your PATH.

The process in divided in 3 parts.
Compiling : Read and transform the Python into machines instructions contained inside an object file.
Linking : Combine the generated object file with Python runtime to generate an executable program.
Running : Run the generated program. Generated exe file will try to find an existing python installation on the setup.
"""
import platform
from shutil import copyfile
import sys
import os
from pathlib import Path
from subprocess import PIPE, Popen
from sys import stderr, stdin, stdout
from typing import Any

import flyable.compiler as com
import flyable.tool.platform as plat
from flyable import constants
from flyable.debug.code_branch_viewer import BranchViewer
from flyable.debug.debug_flags import DebugFlag, DebugFlagListType, enable_debug_flags
from flyable.debug.debug_flags_list import *
from flyable.tool.utils import end_step, add_step

ENABLED_DEBUG_FLAGS: DebugFlagListType = [
]
"""
Debug flags to be enabled during the compiling, the linking and the running process\n
Pass a flag alone to enable it or pass a tuple to also give it a value
"""


def main(file: str, output_dir: str = ".", exec_name: str = "a"):
    add_step("Compiling")

    compiler = com.Compiler()
    compiler.add_file(file)
    compiler.set_output_path(f"{output_dir}/output.o")
    # Make sur the folder exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    compiler.compile()

    end_step()

    if not compiler.has_error():
        # Link the object file
        add_step("Linking")

        # Now link the code
        linker_args = [
            "gcc",
            "-flto",
            "output.o",
            constants.PYTHON_3_11_PATH,
        ]

        if platform.system() == "Windows":
            linker_args.append(constants.PYTHON_3_11_DLL_PATH)

        p = Popen(linker_args, cwd=output_dir)
        p.wait()
        if p.returncode != 0:
            raise Exception("Linking error")

        end_step()


def run_code(output_dir: str, exec_name: str):
    """Runs the code

    Args:
        output_dir (str): the directory where the code is
        exec_name (str): the name of the executable
    """
    add_step("Running")

    p = Popen(
        [output_dir + "/" + exec_name, os.getcwd() + "\\test.py"],
        cwd=os.path.dirname(os.path.realpath(sys.executable)),
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        text=True,
    )

    p.communicate()
    end_step()

    print("-------------------")

    print("Application ended with code " + str(p.returncode))


if __name__ == "__main__":
    # toggles on the debug flags
    enable_debug_flags(*ENABLED_DEBUG_FLAGS)
    dir = f"./build/{plat.get_platform_folder()}"

    if platform.system() == "Windows":
        # move dll to executable location
        copyfile(constants.PYTHON_3_11_DLL_PATH, f"{dir}/python311.dll")

    main("test.py", dir, "a")
    run_code("./build/win64/", "a")

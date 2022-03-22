from __future__ import annotations
from shutil import copyfile
import sys
from typing import TYPE_CHECKING

from flyable.compiler import Compiler
from tests.quail.testers.compiler_tester import FlyCompilerTester

if TYPE_CHECKING:
    from tests.quail.utils.utils import StdOut
    from typing import Literal

import os
import platform
from dataclasses import dataclass, field
from subprocess import Popen, PIPE

from flyable import constants
from tests.quail.utils.utils import CompilationError


@dataclass
class QuailTest:
    file_name: str
    mode: Literal["compile", "runtime", "both"] = "runtime"
    infos: dict[str, str] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    original_lines: list[str] = field(default_factory=list)

    temp_working_dir: str = field(default='generated_scripts', init=False)

    def is_valid_or_raise(self):
        if "Name" not in self.infos:
            raise AttributeError("Each test must have a Name")

    def py_compile(self):
        return compile("".join(self.lines), self.file_name, "exec")

    def fly_compile(self, save_results: bool = False):
        temp_working_dir = self.temp_working_dir
        if not os.path.exists(temp_working_dir):
            os.makedirs(temp_working_dir)
        function_file_temp_path = f"{temp_working_dir}/{self.name}.py"
        with open(function_file_temp_path, "w+") as python_file:
            python_file.write("".join(self.lines))

        compiler = Compiler() if not save_results else FlyCompilerTester()
        compiler.add_file(function_file_temp_path)
        compiler.set_output_path(f"{temp_working_dir}/output.o")

        try:
            compiler.compile()
        except Exception as e:
            raise CompilationError(f"COMPILATION_ERROR: {e}")

        if not compiler.has_error():
            return compiler

        raise CompilationError(compiler.get_errors())

    def fly_exec(self, stdout: StdOut):
        if platform.system() == "Windows":
            # move dll to executable location
            copyfile(constants.PYTHON_3_11_DLL_PATH, f"{self.temp_working_dir}/python311.dll")
    
        self.fly_compile()
        # Now link the code
        linker_args = [
            "gcc",
            "-flto",
            "output.o",
            constants.PYTHON_3_11_PATH,
        ]

        if platform.system() == "Windows":
            linker_args.append(constants.PYTHON_3_11_DLL_PATH)

        p0 = Popen(linker_args, cwd=self.temp_working_dir)
        p0.wait()
        if p0.returncode != 0:
            raise CompilationError("Linking error")

        p = Popen(
            [self.temp_working_dir + "/" + "a.exe", os.path.realpath(f"{self.temp_working_dir}\\{self.name}.py")],
            cwd=os.path.dirname(os.path.realpath(sys.executable)),
            stdout=PIPE,
            text=True
        )

        if isinstance(p, str):
            raise CompilationError(p)
        print(p.communicate()[0], end="")
        result = stdout.content
        stdout.clear()
        return result

    def py_exec(self, stdout: StdOut):
        exec(self.py_compile(), {}, {})
        result = stdout.content
        stdout.clear()
        if not all(x == "True" for x in result.split("\n") if x):
            raise Warning(result)

        return result

    @property
    def name(self):
        return self.infos["Name"]

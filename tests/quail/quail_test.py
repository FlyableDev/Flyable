from __future__ import annotations
from typing import TYPE_CHECKING

from flyable.compiler import Compiler

if TYPE_CHECKING:
    from tests.quail.utils.utils import StdOut
    from typing import Literal

import os
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

    def is_valid_or_raise(self):
        if "Name" not in self.infos:
            raise AttributeError("Each test must have a Name")

    def py_compile(self):
        return compile("".join(self.lines), self.file_name, "exec")

    def fly_compile(self):
        temp_working_dir = f'generated_scripts'
        if not os.path.exists(temp_working_dir):
            os.makedirs(temp_working_dir)
        function_file_temp_path = f"{temp_working_dir}/{self.file_name}"
        with open(function_file_temp_path, "w+") as python_file:
            python_file.write("".join(self.lines))

        compiler = Compiler()
        compiler.add_file(function_file_temp_path)
        compiler.set_output_path(f"{temp_working_dir}/output.o")

        try:
            compiler.compile()
        except Exception as e:
            return f"COMPILATION_ERROR: {e}"

        if not compiler.has_error():
            linker_args = [
                "gcc",
                "-flto",
                "output.o",
                constants.LIB_FLYABLE_RUNTIME_PATH,
                constants.PYTHON_3_10_PATH,
            ]
            p = Popen(linker_args, cwd=temp_working_dir)
            p.wait()
            if p.returncode != 0:
                raise CompilationError("Linking error")

            p2 = Popen(
                [temp_working_dir + f"/a.exe"],
                cwd=temp_working_dir,
                stdout=PIPE,
                text=True
            )
            return p2

        raise CompilationError(compiler.get_errors())

    def fly_exec(self, stdout: StdOut):
        p = self.fly_compile()
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
        return result

    @property
    def name(self):
        return self.infos["Name"]

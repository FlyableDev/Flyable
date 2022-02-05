from __future__ import annotations

from enum import Enum, auto
import os
from subprocess import PIPE, Popen
from sys import stderr, stdin, stdout
import tempfile
from typing import TYPE_CHECKING
from flyable import constants
import flyable.compiler as com

if TYPE_CHECKING:
    from tests.tools.tests_separated.utils.body_test_parser import BodyTestParser

from dataclasses import dataclass, field
from typing import Optional, Callable


@dataclass
class StdOut:
    content: str = ""
    write_calls: int = 0

    def clear(self):
        self.content = ''
        self.write_calls = 0


class BodyTestState(Enum):
    New = auto()
    Infos = auto()
    Body = auto()
    End = auto()
    None_ = auto()


@dataclass
class BodyTest:
    file_name: str
    infos: dict[str, str] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def is_valid_or_raise(self):
        if "Name" not in self.infos:
            raise AttributeError("Each test must have a Name")

    def py_compile(self):
        return compile("".join(self.lines), self.file_name, "exec")

    def fly_compile(self):
        #temp_working_dir = tempfile.mkdtemp()
        temp_working_dir = f'generated_scripts'
        function_file_temp_path = f"{temp_working_dir}/{self.file_name}.py"#os.path.join(temp_working_dir, f"{self.file_name}.py")
        python_file = open(function_file_temp_path, "a")
        python_file.write("\n".join(self.lines))

        compiler = com.Compiler()
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
                raise Exception("Linking error")

            
            p2 = Popen(
                [temp_working_dir + f"/a.exe"],
                cwd=temp_working_dir,
                stdout=PIPE,
                text=True
            )

            print(p2.communicate()[0])
            


    @property
    def name(self):
        return self.infos["Name"]


# ********************** tag functions **********************
def tag_new(args: list[str], test: BodyTestParser) -> BodyTestState:
    if test.current_state is not BodyTestState.None_:
        raise ValueError("You must end a test before starting a new one")
    return BodyTestState.New


def tag_start(args: list[str], test: BodyTestParser) -> BodyTestState:
    if test.current_state is BodyTestState.None_:
        raise ValueError("You must create a test before defining its body")
    return BodyTestState.Body


def tag_end(args: list[str], test: BodyTestParser) -> BodyTestState:
    if test.current_state is not BodyTestState.Body:
        raise ValueError("You must create a test before defining its body")
    return BodyTestState.End


TAGS: dict[str, Callable[[list[str], BodyTestParser], BodyTestState]] = {
    "new": tag_new,
    "start": tag_start,
    "end": tag_end,
}
TAG_START = r" *# *Flytest:\w+.*"
FLY_TEST_INFOS: list[str] = ["Name", "Flyable-version", "Description"]

from typing import Sequence, List
import flyable.compiler as com
import flyable.tool.platform as plat
from subprocess import Popen, PIPE
from pathlib import Path
import platform

"""
To test Flyable we run a bunch of example and look at the output of it. It the outputs correspond to the expected
result the test is considered to be successful.
"""


class Test:

    def setup(self, output_dir: str, source_dir: str):
        self.__output_dir = output_dir
        self.__source_dir = source_dir
        self.__files: List[str] = []
        self.__expected_results: List[Sequence[str]] = []

    def add_test(self, file_name: str, *results: str):
        self.__files.append(file_name)
        self.__expected_results.append(results)

    def run(self):
        for file, expected_result in zip(self.__files, self.__expected_results):
            self.__run_test(file, expected_result)

    def __run_test(self, file_name: str, expected_outputs: List[str]):
        file_name = f"{self.__source_dir}/{file_name}"
        output_dir = f"{self.__output_dir}/{plat.get_platform_folder()}"
        compiler = com.Compiler()
        compiler.add_file(file_name)
        compiler.set_output_path(f"{output_dir}/output.o")
        # Make sur the folder exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        compiler.compile()

        if not compiler.has_error():
            # Now link the code
            python_lib = "python310.lib" if platform.system() == "Windows" else "python3.10.a"
            linker_args = ["gcc", "-flto", "output.o",
                           "libFlyableRuntime.a", python_lib]
            p = Popen(linker_args, cwd=output_dir)
            p.wait()
            # assert p.returncode != 0, "Linking error"

            p2 = Popen([f"{output_dir}/a.exe"],
                      cwd=output_dir, stdin=PIPE, stdout=PIPE, text=True, encoding="utf8")

            outputs, err = p2.communicate()

            for output, expected_output in zip(outputs.replace("\r", "").split("\n"), expected_outputs):
                assert output == expected_output, f"❌ {file_name=}, {expected_output=}, {output=}"

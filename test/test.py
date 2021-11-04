import flyable.compiler as com
import flyable.tool.platform as plat
from subprocess import Popen, PIPE
from pathlib import Path
import platform

"""
To test Flyable we run a bunch of example and look at the output of it. It the outputs correspond to the expected
result the test is considered to be successful.
"""


def setup_test(test):
    test.add_test("fibonacci.py", "55")
    #test.add_test("cond.py", "YYY")


class Test:

    def __init__(self):
        self.__files = []
        self.__expected_results = []

    def add_test(self, file_name, result):
        self.__files.append(file_name)
        self.__expected_results.append(result)

    def run(self):
        for i, _ in enumerate(self.__files):
            self.__run_test(self.__files[i], self.__expected_results[i])

    def __run_test(self, file_name, expected_print):
        file_name = "src/" + file_name
        compiler = com.Compiler()
        compiler.add_file(file_name)
        compiler.set_output_path("../build/" + plat.get_platform_folder() + "/output.o")
        Path("build").mkdir(parents=True, exist_ok=True)  # Make sur the folder exist
        compiler.compile()

        if not compiler.has_error():
            # Now link the code
            python_lib = "python39.lib" if platform.system() == "Windows" else "python3.9.a"
            linker_args = ["gcc", "-flto", "output.o", "libFlyableRuntime.a", python_lib]
            p = Popen(linker_args, cwd="..\\build\\" + plat.get_platform_folder())
            p.wait()
           # assert p.returncode != 0, "Linking error"

            p = Popen(["../build/" + plat.get_platform_folder() +
                       "/a.exe"], cwd="..\\build\\" + plat.get_platform_folder(), stdin=PIPE, stdout=PIPE)
            output, err = p.communicate()

            assert output == expected_print, f"{file_name=}, {output=}"


if __name__ == "__main__":
    test = Test()
    setup_test(test)
    test.run()

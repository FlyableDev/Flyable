"""
Here is an example on how to use Flyable.
You need to have the GCC compiler in your PATH.

The process in divided in 3 parts.
Compiling : Read and transform the Python into machines instructions contained inside an object file.
Linking : Combine the generated object file with Python runtime to generate an executable program.
Running : Run the generated program. Generated exe file will try to find an existing python installation on the setup.
"""

import flyable.compiler as com
import flyable.tool.platform as plat
from subprocess import Popen, PIPE
from pathlib import Path
import platform


def main():
    print("Compiling....")

    compiler = com.Compiler()
    compiler.add_file("test.py")
    compiler.set_output_path("../build/" + plat.get_platform_folder() + "/output.o")
    Path("build").mkdir(parents=True, exist_ok=True)  # Make sur the folder exist
    compiler.compile()

    if not compiler.has_error():
        # Link the object file
        print("Linking.....")

        # Now link the code
        python_lib = "python39.lib" if platform.system() == "Windows" else "python3.9.a"
        linker_args = ["gcc", "-flto", "output.o", "libFlyableRuntime.a", python_lib]
        p = Popen(linker_args, cwd="..\\build\\" + plat.get_platform_folder())
        p.wait()
        if p.returncode != 0:
            raise Exception("Linking error")

        # Now run the code
        print("running...")
        p = Popen(["../build/" + plat.get_platform_folder() +
                   "/a.exe"], cwd="..\\build\\" + plat.get_platform_folder(), stdin=PIPE, stdout=PIPE)
        output, err = p.communicate()

        print("-------------------")
        print(output.decode())  # Print what the program outputted

        print("Application ended with code " + str(p.returncode))


if __name__ == '__main__':
    main()

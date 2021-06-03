"""
Here is an example on how to use Flyable.
You need to have the GCC compiler in your PATH.

The process in divided in 3 parts.
Compiling : Read and transform the Python into machines instructions contained inside an object file.
Linking : Combine the generated object file with Python runtime to generate an executable program.
Running : Run the generated program. Generated exe file will try to find an existing python installation on the setup.
"""

import flyable.compiler as com
from subprocess import Popen, PIPE


def main():
    print("Compiling....")

    compiler = com.Compiler()
    compiler.add_file("test.py")
    compiler.set_output_path("build/output.o")
    compiler.compile()

    # Link the object file
    print("Linking.....")

    # Now link the code
    p = Popen(["gcc", "output.o", "libFlyableRuntime.a", "python39.lib"], cwd="build")
    p.wait()
    if p.returncode != 0: raise Exception("Linking error")

    # Now run the code
    print("running...")
    p = Popen(["build/a.exe"], cwd="build", stdin=PIPE, stdout=PIPE)
    output, err = p.communicate()

    print("-------------------")
    print(output.decode())  # Print what the program outputted


if __name__ == '__main__':
    main()

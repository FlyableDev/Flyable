import os
from flyableTests.test import Test

#-------------------- setup, run and clean up for the tests --------------------#

def setup_test(file: str, prefix: str = "test"):
    lines_before_test: list[str]
    with open(f"flyableTests/tests/{file}", "r") as f:
        lines_before_test = f.readlines()

    with open(f"flyableTests/tests/{prefix}-{file}", "w+") as f:
        # we need to add an input at the end of the file because otherwise,
        # it won't register the output in stdout 
        # (idk why, but this is how i got it working)
        f.writelines(lines_before_test + ["\ninput()"])

    def clean_up(dir: str):
        os.remove(f"{dir}/a.exe")
        os.remove(f"{dir}/output.o")
        os.remove(f"flyableTests/tests/{prefix}-{file}")

    return clean_up


def run_test(file: str, *expected_outputs: str, prefix: str = "test"):
    test = Test()
    test.setup(output_dir="build-test", source_dir="flyableTests/tests")

    clean_up = setup_test(file, prefix=prefix)

    try:
        test.add_test(f"{prefix}-{file}", *expected_outputs)
        test.run()
    finally:
        clean_up("build-test/win64")

#-------------------- Add your tests here --------------------#

def test_arithmetic():
    run_test("arithmetic.py")


def test_cond():
    run_test("cond.py", "Y", "Y", "Y")


def test_fibo():
    run_test("fibonacci.py", "55")


"""
How to add another test:
1. create a file .py in flyableTests/tests
2. in this file, create a function
3. call run_test inside that function with the following parameters:
    - the name of the file you want to test in flyableTests/tests
    - the expected outputs of running your file
4. install pytest
5. call (in the terminal): pytest test.py
6. congratulations, you added a new test! 🎉🎉🎉
"""

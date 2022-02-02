import os
import shutil
from sys import stderr, stdin, stdout
import tempfile
from typing import Any

import pytest
import inspect

from _pytest.fixtures import SubRequest

import flyable.compiler as com
from flyable import constants
from subprocess import Popen, PIPE


@pytest.fixture()
def compiled_value(request: SubRequest):
    """
    Extracts the python code from the current test function into a temporary python file that is then compiled.
    The result is then injected in the Python test so the compiled value can be compared with the Python value.
    """
    function_name = request.function.__name__
    temp_working_dir = tempfile.mkdtemp()
    path = f'./generated_scripts/{function_name}.py'
    function_file_temp_path = path #os.path.join(path, f"{function_name}.py")
    try:
        _remove_old_python_file(function_file_temp_path)
        _generate_current_test_python_file(function_file_temp_path, function_name, request)
        print(function_file_temp_path)
        res = get_compiled_value_from_test_file(function_file_temp_path, temp_working_dir)
        return res
    finally:
        shutil.rmtree(temp_working_dir)


def _generate_current_test_python_file(function_file_temp_path: str, function_name: str, request):
    python_file = None
    test_function_indentation = None
    for code_line in inspect.getsourcelines(request.module)[0]:
        code_line = code_line.replace('\n', '')

        # Creating new python file for current testcase
        if python_file is None and f"def {function_name}" in code_line:
            test_function_indentation = _get_line_indentation(code_line)
            # Removes the "compiled_value" argument since it's an injected fixture for the python's test execution
            code_line = code_line.replace("compiled_value", "")
            python_file = open(function_file_temp_path, "a")
            python_file.write(code_line + "\n")
            continue
        
        # Write operations on python file
        if python_file is None:
            continue

        # Replaces the assertion with a return statement so the compiler returns a value for us to compare
        if "assert" in code_line and python_file is not None:
            code_line = code_line.replace("compiled_value", "")
            code_line = code_line.replace("==", "")
            code_line = code_line.replace("assert", "return")

        # Add print of function call
        if _is_end_of_test_function_reached(test_function_indentation, code_line):
            # Prints the function's result at the end of the file so we can extract it when running the .exe
            python_file.write(f"print({function_name}())")
            python_file.close()
            return
        else: 
            # Write line to python file
            python_file.write(code_line + "\n")




def _is_end_of_test_function_reached(test_function_indentation: int, code_line: str) -> bool:
    return test_function_indentation is not None and _get_line_indentation(code_line) == \
                test_function_indentation


def _get_line_indentation(line: str) -> int:
    return len(line) - len(line.lstrip())


def get_compiled_value_from_test_file(file_name: str, output_dir: str) -> Any:
    compiler = com.Compiler()
    compiler.add_file(file_name)
    compiler.set_output_path(f"{output_dir}/output.o")
    try:
        compiler.compile()
    except Exception as e:
        return f"COMPILATION_ERROR: {e}"

    if not compiler.has_error():
        linker_args = ["gcc", "-flto", "output.o",
                       constants.LIB_FLYABLE_RUNTIME_PATH, constants.PYTHON_3_10_PATH]
        
        p = Popen(linker_args, cwd=output_dir)
        p.wait()

        if p.returncode != 0:
            raise Exception("Linking error")

        p2 = Popen([f"{output_dir}/a.exe"], cwd=output_dir, stdin=PIPE, stdout=PIPE, text=True, encoding="utf8")
        
        outputs, errors = p2.communicate()
        
        if outputs is None or outputs == "":
            raise Exception(f"No assert statement in function")

        return eval(outputs)


def _remove_old_python_file(path): 
    if os.path.exists(path):
        os.remove(path)
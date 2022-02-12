import sys, os
from functools import wraps
from os import path
from typing import Callable

import pytest
from _pytest.fixtures import SubRequest
from tests.quail.parser.parser import parse_quailt_file
from tests.quail.quail_test import QuailTest
from tests.quail.utils.utils import StdOut, CompilationError


def _get_error_msg(test, py_result, fly_result):
    return (
            f"python  => {py_result}\n"
            f"flyable => {fly_result}\n"
            + "-" * 15
            + "tested code"
            + "-" * 15
            + f"\n{''.join(test.lines)}\n"
            + (
                "-" * 15 + "original code" + "-" * 15 + f"\n{''.join(test.original_lines)}"
                if test.original_lines != test.lines
                else ""
            )
    )


def flytest(func: Callable):
    @wraps(func)
    def inner(*args, **kwargs):
        quail_test_name = func.__name__.split("test_", 1)[1]
        if "quail_test" in kwargs:
            if quail_test_name not in kwargs["quail_test"]:
                raise NameError(f"There are no Quail test with name '{quail_test_name}'")
            kwargs["quail_test"] = kwargs["quail_test"][quail_test_name]
        return func(*args, **kwargs)

    return inner


def flytest_runtimes(
        func: Callable = None, include: list[str] = None, exclude: list[str] = None
):
    if include is not None and exclude is not None:
        raise AttributeError("You cannot include and exclude at the same time")

    def test_flytest_runtimes(quail_test: dict[str, QuailTest], stdout: StdOut):
        failed: list = []
        for test in quail_test.values():
            if (
                    test.mode not in ("runtime", "both")
                    or (exclude and test.name in exclude)
                    or (include and test.name not in include)
            ):
                continue

            py_result = test.py_exec(stdout).split("\n")
            try:
                fly_result = test.fly_exec(stdout).split("\n")
                if py_result != fly_result:
                    failed.append(
                        f"Failed test '{test.name}':\n"
                        + _get_error_msg(test, py_result, fly_result)
                    )
            except CompilationError as e:
                failed.append(
                    f"Failed test '{test.name}' (while compiling: {e}):\n"
                    + _get_error_msg(test, py_result, "ERROR")
                )

        assert not failed, "\n".join(failed)

    if func is None:
        def wrap(_: Callable):
            return test_flytest_runtimes

        return wrap

    return test_flytest_runtimes


def get_quail_tests(dir_name: str, current_file_path: str) -> dict:
    # removes the extension .py
    current_file_name = path.basename(current_file_path)[:-3]
    test_quailt_file_name = "quailt_" + current_file_name.split("_", 1)[1] + ".py"
    test_quailt_file_path = (
            dir_name + "/" + path.dirname(current_file_path) + test_quailt_file_name
    )
    parsed_tests = parse_quailt_file(test_quailt_file_path)

    return parsed_tests


@pytest.fixture(scope="module")
def quail_test(request: SubRequest):
    return get_quail_tests(
        request.fspath.dirname, os.getenv("PYTEST_CURRENT_TEST").split("::")[0]
    )


@pytest.fixture
def stdout(monkeypatch):
    buffer = StdOut()

    def fake_write(s):
        buffer.content += s
        buffer.write_calls += 1

    monkeypatch.setattr(sys.stdout, "write", fake_write)
    yield buffer
    buffer.clear()

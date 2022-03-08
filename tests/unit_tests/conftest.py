from __future__ import annotations
from typing import TYPE_CHECKING

from _pytest.config import Config
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.reports import CollectReport, TestReport
from _pytest.runner import CallInfo

if TYPE_CHECKING:
    from _pytest.config.argparsing import Parser
    from _pytest.mark.structures import Node, Mark

import sys, os
from functools import wraps
from os import path
from typing import Callable, Optional

import pytest
from _pytest.fixtures import SubRequest
from tests.quail.parser.parser import parse_quailt_file
from tests.quail.quail_test import QuailTest
from tests.quail.utils.utils import StdOut, CompilationError


def _get_error_msg(test, py_result, fly_result, dependencies=None):
    return (
        (
            f"\n/!\\ This test might have failed be because of one of the dependencies "
            f"{tuple(dependencies.replace(' ', '').split(','))!r} /!\\.\n\n"
            if dependencies is not None
            else ""
        )
        + f"python  => {py_result}\n"
        + f"flyable => {fly_result}\n"
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


def _get_warning_msg(warnings: list[tuple[str, list[str]]]):
    warning = "\n".join(
        f"- {test_name} (outputs => {py_result})" for test_name, py_result in warnings
    )
    return (
        "\n\nThe following tests had some values evaluated to False when executed with python:\n"
        + warning
        + "\n"
        + "-" * 15
    )


def quail_tester(func: Callable):
    @wraps(func)
    def inner(*args, **kwargs):
        nonlocal func
        quail_test_name = func.__name__.split("test_", 1)[1]

        def quail_test_in(category: str):
            if quail_test_name not in kwargs[category]:
                raise NameError(
                    f"There are no Quail test with name '{quail_test_name}'"
                )
            return True

        if "quail_test" in kwargs and quail_test_in("quail_test"):
            dependencies = kwargs["quail_test"][quail_test_name].infos.get(
                "Dependencies"
            )
            if dependencies is not None:
                pytest.mark.depends_on(*dependencies.replace(" ", "").split(","))(func)

            kwargs["quail_test"] = kwargs["quail_test"][quail_test_name]

        if "quail_results" in kwargs and quail_test_in("quail_results"):
            kwargs["quail_results"] = (
                kwargs["quail_results"][quail_test_name]
                .fly_compile(save_results=True)
                .results
            )
        return func(*args, **kwargs)

    return inner


def quail_runtimes_tester(
    func: Callable = None,
    include: list[str] = None,
    exclude: list[str] = None,
    strict: bool = False,
    mode: str = "",
):
    """
    This method wraps an empty method and will test the execution of every quail test found
    in the quailt_<x>.py file not marked with the "compiler" argument for the "Quail-test:new" tag
    """
    if include is not None and exclude is not None:
        raise AttributeError("You cannot include and exclude at the same time")

    def test_quail_test_runtimes(quail_test: dict[str, QuailTest], stdout: StdOut):
        failed: list[str] = []
        warnings: list[tuple[str, list[str]]] = []
        for test in quail_test.values():
            if (
                test.mode not in ("runtime", "both")
                or (exclude and test.name in exclude)
                or (include and test.name not in include)
            ):
                continue
            try:
                py_result = test.py_exec(stdout).split("\n")
            except Warning as e:
                py_result = e.args[0].split("\n")
                warnings.append((test.name, py_result))

            try:
                fly_result = test.fly_exec(stdout).split("\n")
                if fly_result[-1] == "" and py_result[-1] == "":
                    fly_result = fly_result[:-1]
                    py_result = py_result[:-1]

                if py_result != fly_result:
                    failed.append(
                        f"Failed test '{test.name}':\n"
                        + _get_error_msg(
                            test, py_result, fly_result, test.infos.get("Dependencies")
                        )
                    )
            except CompilationError as e:
                failed.append(
                    f"Failed test '{test.name}' (while compiling: {e}):\n"
                    + _get_error_msg(test, py_result, "ERROR")
                )

        # if strict mode enabled and there are warnings
        assert not strict or not warnings, _get_warning_msg(warnings)

        # if some tests failed
        assert not failed, "\n" + ("\n" + "~" * 30 + "\n\n").join(failed)

    if func is None:

        def wrap(_: Callable):
            return test_quail_test_runtimes

        return wrap

    return test_quail_test_runtimes


QUAIL_TESTS: dict


def get_quail_tests(dir_name: str, current_file_path: str) -> dict:
    # removes the extension .py
    global QUAIL_TESTS
    current_file_name = path.basename(current_file_path)[:-3]
    test_quailt_file_name = "quailt_" + current_file_name.split("_", 1)[1] + ".py"
    test_quailt_file_path = dir_name + "/" + test_quailt_file_name
    parsed_tests = parse_quailt_file(test_quailt_file_path)
    QUAIL_TESTS = parsed_tests
    return parsed_tests


@pytest.fixture(scope="module")
def quail_test(request: SubRequest):
    return get_quail_tests(
        request.fspath.dirname, os.getenv("PYTEST_CURRENT_TEST").split("::")[0]
    )


@pytest.fixture(scope="module")
def quail_results(request: SubRequest):
    """
    Must be combined with the decorator @quail_tester

    :returns the result of the compiler as a _CompilerResult

    """
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


# ######################### markers #########################


def get_dependencies(item: Node):
    mark: Mark | None = None
    has_dependencies = any(
        "depends_on" == _mark.name and (mark := _mark) for _mark in item.iter_markers()
    )
    if has_dependencies and mark is not None:
        return mark.args
    return None


def pytest_exception_interact(
    node: Node, call: CallInfo, report: CollectReport | TestReport
):
    dependencies = get_dependencies(node)
    if report.failed and dependencies is not None:
        msg = f"\n\n/!\\ This test might have failed be because of one of the dependencies {tuple(dependencies)!r} /!\\."
        print(msg, file=sys.stderr)


def pytest_runtest_call(item: Item):
    name = item.name.replace("test_", "")
    if name in QUAIL_TESTS:
        dependencies = QUAIL_TESTS[name].infos.get("Dependencies")
        if dependencies is not None:
            item.add_marker(
                pytest.mark.depends_on(*dependencies.replace(" ", "").split(","))
            )
    item.runtest()

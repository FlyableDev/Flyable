import sys, os
from functools import wraps
from os import path
from typing import Callable

import pytest
from _pytest.fixtures import SubRequest
from tests.unit_tests.utils.body_test_parser import parse_body_test_file
from tests.unit_tests.utils.utils import StdOut


def flytest(func: Callable):
    @wraps(func)
    def inner(*args, **kwargs):
        body_name = func.__name__.split("test_", 1)[1]
        if "body_test" in kwargs:
            kwargs["body_test"] = kwargs["body_test"][body_name]
        return func(*args, **kwargs)

    return inner


def get_body_of_tests(dir_name: str, current_file_path: str) -> dict:
    current_file_name = path.basename(current_file_path)[:-3]  # removes the extension .py
    test_body_file_name = "body_" + current_file_name.split("_", 1)[1] + ".py"
    test_body_file_path = dir_name + "/" + path.dirname(current_file_path) + test_body_file_name
    parsed_tests = parse_body_test_file(test_body_file_path)

    return parsed_tests


@pytest.fixture(scope="module", name="body_test")
def body_test(request: SubRequest):
    return get_body_of_tests(request.fspath.dirname, os.getenv('PYTEST_CURRENT_TEST').split("::")[0])


@pytest.fixture
def stdout(monkeypatch):
    buffer = StdOut()

    def fake_write(s):
        buffer.content += s
        buffer.write_calls += 1

    monkeypatch.setattr(sys.stdout, 'write', fake_write)
    yield buffer
    buffer.clear()

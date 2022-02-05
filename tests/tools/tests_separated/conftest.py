from functools import wraps
from os import path
from types import FunctionType

import pytest
from tests.tools.tests_separated.utils.body_test_parser import parse_body_test_file


def flytest(func: FunctionType):
    @wraps(func)
    def inner(*args, **kwargs):
        body_name = func.__name__.split("test_", 1)[1]
        if "test_body" in kwargs:
            kwargs["test_body"] = kwargs["test_body"][body_name]
        return func(*args, **kwargs)

    return inner


def get_body_of_tests(current_file_path: str) -> dict:
    current_file_name = path.basename(current_file_path)[:-3]  # removes the extension .py
    test_body_file_name = "body_" + current_file_name.split("_", 1)[1] + ".py"
    test_body_file_path = path.dirname(current_file_path) + test_body_file_name
    parsed_tests = parse_body_test_file(test_body_file_path)

    return parsed_tests


@pytest.fixture(scope="module", name="test_body")
def get_body_test():
    return get_body_of_tests("test_str.py")

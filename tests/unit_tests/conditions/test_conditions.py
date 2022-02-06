from tests.unit_tests.conftest import flytest
from tests.unit_tests.utils.utils import BodyTest, StdOut


@flytest
def test_if_statement(body_test: BodyTest, stdout: StdOut):
    assert body_test.py_exec(stdout) == body_test.fly_exec(stdout)


@flytest
def test_if_else_statement(body_test: BodyTest, stdout: StdOut):
    assert body_test.py_exec(stdout) == body_test.fly_exec(stdout)


@flytest
def test_if_elif_statement(body_test: BodyTest, stdout: StdOut):
    assert body_test.py_exec(stdout) == body_test.fly_exec(stdout)


@flytest
def test_if_elif_else_statement(body_test: BodyTest, stdout: StdOut):
    assert body_test.py_exec(stdout) == body_test.fly_exec(stdout)


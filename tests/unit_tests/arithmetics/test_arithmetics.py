from tests.unit_tests.conftest import flytest
from tests.unit_tests.tools.utils import BodyTest, StdOut


@flytest
def test_addition(body_test: BodyTest, stdout: StdOut):
    assert body_test.fly_exec(stdout) == body_test.py_exec(stdout)


@flytest
def test_subtraction(body_test: BodyTest, stdout: StdOut):
    assert body_test.fly_exec(stdout) == body_test.py_exec(stdout)


@flytest
def test_multiplication(body_test: BodyTest, stdout: StdOut):
    assert body_test.fly_exec(stdout) == body_test.py_exec(stdout)


@flytest
def test_division(body_test: BodyTest, stdout: StdOut):
    assert body_test.fly_exec(stdout) == body_test.py_exec(stdout)


@flytest
def test_division_by_zero(body_test: BodyTest, stdout: StdOut):
    assert body_test.fly_exec(stdout) == body_test.py_exec(stdout)


@flytest
def test_modulo(body_test: BodyTest, stdout: StdOut):
    assert body_test.fly_exec(stdout) == body_test.py_exec(stdout)


@flytest
def test_pow(body_test: BodyTest, stdout: StdOut):
    assert body_test.fly_exec(stdout) == body_test.py_exec(stdout)


@flytest
def test_floor_division(body_test: BodyTest, stdout: StdOut):
    assert body_test.fly_exec(stdout) == body_test.py_exec(stdout)

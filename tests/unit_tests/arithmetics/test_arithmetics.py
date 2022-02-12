from tests.unit_tests.conftest import flytest
from tests.quail.utils.utils import StdOut
from tests.quail.quail_test import QuailTest


@flytest
def test_addition(quail_test: QuailTest, stdout: StdOut):
    assert quail_test.fly_exec(stdout) == quail_test.py_exec(stdout)


@flytest
def test_substraction(quail_test: QuailTest, stdout: StdOut):
    assert quail_test.fly_exec(stdout) == quail_test.py_exec(stdout)


@flytest
def test_multiplication(quail_test: QuailTest, stdout: StdOut):
    assert quail_test.fly_exec(stdout) == quail_test.py_exec(stdout)


@flytest
def test_division(quail_test: QuailTest, stdout: StdOut):
    assert quail_test.fly_exec(stdout) == quail_test.py_exec(stdout)


@flytest
def test_division_by_zero(quail_test: QuailTest, stdout: StdOut):
    assert quail_test.fly_exec(stdout) == quail_test.py_exec(stdout)


@flytest
def test_modulo(quail_test: QuailTest, stdout: StdOut):
    assert quail_test.fly_exec(stdout) == quail_test.py_exec(stdout)


@flytest
def test_pow(quail_test: QuailTest, stdout: StdOut):
    assert quail_test.fly_exec(stdout) == quail_test.py_exec(stdout)


@flytest
def test_floor_division(quail_test: QuailTest, stdout: StdOut):
    assert quail_test.fly_exec(stdout) == quail_test.py_exec(stdout)

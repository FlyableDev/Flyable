from tests.unit_tests.conftest import flytest
from tests.unit_tests.utils.utils import BodyTest, StdOut


@flytest
def test_int_equality(body_test: BodyTest, stdout: StdOut):
    assert body_test.py_exec(stdout) == body_test.fly_exec(stdout)


@flytest
def test_float_equality(body_test: BodyTest, stdout: StdOut):
    assert body_test.py_exec(stdout) == body_test.fly_exec(stdout)


@flytest
def test_bool_equality(body_test: BodyTest, stdout: StdOut):
    assert body_test.py_exec(stdout) == body_test.fly_exec(stdout)


@flytest
def test_triple_equality(body_test: BodyTest, stdout: StdOut):
    assert body_test.py_exec(stdout) == body_test.fly_exec(stdout)


@flytest
def test_is_operator(body_test: BodyTest, stdout: StdOut):
    assert body_test.py_exec(stdout) == body_test.fly_exec(stdout)


@flytest
def test_zero_and_one_bool_comparison_with_is(body_test: BodyTest, stdout: StdOut):
    assert body_test.py_exec(stdout) == body_test.fly_exec(stdout)


@flytest
def test_zero_and_one_bool_comparison_with_equal(body_test: BodyTest, stdout: StdOut):
    assert body_test.py_exec(stdout) == body_test.fly_exec(stdout)

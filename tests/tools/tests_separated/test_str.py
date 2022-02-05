from tests.tools.tests_separated.conftest import flytest
from tests.tools.tests_separated.utils.utils import BodyTest, StdOut


@flytest
def test_empty_str_creation(body_test: BodyTest, stdout: StdOut):
    exec(body_test.py_compile())
    python_exec = stdout.content
    stdout.clear()

    body_test.fly_compile()
    fly_exec = stdout.content
    stdout.clear()

    assert python_exec == fly_exec


@flytest
def test_len_str(body_test: BodyTest, stdout: StdOut):
    pass

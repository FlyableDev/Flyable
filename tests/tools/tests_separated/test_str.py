from tests.tools.tests_separated.conftest import flytest
from tests.tools.tests_separated.utils.utils import BodyTest, StdOut


@flytest
def test_empty_str_creation(body_test: BodyTest, stdout: StdOut):
    assert body_test.py_exec_matches_flyable_exec(stdout)


@flytest
def test_len_str(body_test: BodyTest, stdout: StdOut):
    pass

import pytest

from tests.tools.tests_separated.conftest import flytest
from tests.tools.tests_separated.utils.utils import BodyTest, StdOut


@flytest
def test_empty_str_creation(body_test: BodyTest, stdout: StdOut):
    assert body_test.py_exec(stdout) == body_test.fly_exec(stdout)


@flytest
# @pytest.mark.xfail(reason="known issue")
def test_len_str(body_test: BodyTest, stdout: StdOut):
    assert body_test.py_exec(stdout) == body_test.fly_exec(stdout)

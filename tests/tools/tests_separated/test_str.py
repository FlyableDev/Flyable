from tests.tools.tests_separated.conftest import flytest
from tests.tools.tests_separated.utils.utils import BodyTest


@flytest
def test_empty_str_creation(test_body: BodyTest, stdout_content):
    test_body.py_compile()


@flytest
def test_len_str(test_body: BodyTest, stdout_content):
    pass

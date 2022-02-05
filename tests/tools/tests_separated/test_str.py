from tests.tools.tests_separated.conftest import flytest
from tests.tools.tests_separated.utils.utils import TestBody


@flytest
def test_empty_str_creation(test_body: TestBody):
    test_body.py_compile()


@flytest
def test_len_str(test_body: TestBody):
    pass

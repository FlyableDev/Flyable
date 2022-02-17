from tests.quail.quail_test import QuailTest
from tests.quail.testers.compiler_tester import CompilerResult
from tests.quail.utils.utils import StdOut
from tests.unit_tests.conftest import quail_runtimes_tester, quail_tester


@quail_runtimes_tester
def test_runtimes():
    pass


@quail_tester
def test_func_creation(quail_results: CompilerResult):
    quail_results.assert_func("abc").has_impl(int)
    quail_results.assert_func("gt2").has_impl(int, int)

from __future__ import annotations
from typing import TYPE_CHECKING
from tests.integration.utils import Style
from tests.integration.output.logs import create_log
from tests.integration.output.logs import add_log

if TYPE_CHECKING:
	from tests.integration.integration_test_runner import IntegrationTestRunner as TestRunner

style_print = Style.style_print

class TestOuput:
	def __init__(self, test_runner: TestRunner) -> None:
		self.__runner = test_runner

	@property
	def test(self):
		current_test = self.__runner.get_current_test()
		if current_test is None:
			raise Exception("Error with the TestOutput when trying to show an output when no test is running")
		return current_test

	def test_start(self):
		"""
		Generated output before running a specific test
		"""
		self.print_logger(f"&6-------- Running test {self.__runner.get_current_test_index()}/{self.__runner.get_nb_tests()} --------")

	def test_fly_res(self, fly_res: str):
		self.print_logger(f"&7[FLYABLE - Output of test {self.test.name}]")
		self.print_logger(fly_res)
		self.print_logger(f"&7[FLYABLE - End of output of test {self.test.name}]")
	
	def test_py_res(self, py_res: str):
		self.print_logger(f"&7[PYTHON - Output of test {self.test.name}]")
		self.print_logger(py_res)
		self.print_logger(f"&7[PYTHON - End of output of test {self.test.name}]")

	def test_success(self):
		self.print_logger(f"&a-------- Success running test {self.test.name} --------\n")
	
	def test_failure(self):
		self.print_logger(f"&c-------- Failure running test {self.test.name} --------\n")

	def print_logger(self, text: str):
		style_print(text)

		if self.test.logging():
			add_log(self.test, text)

		if self.__runner.logging():
			pass


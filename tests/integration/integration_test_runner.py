from tests.integration.integration_test import IntegrationTest
from tests.integration.output.test_output import TestOuput


class IntegrationTestRunner:
  
  def __init__(self):
    self.__current_test: IntegrationTest | None = None
    self.__test_index: int = 0
    self.__tests: dict[str, IntegrationTest] = {}
    self.__test_output: TestOuput = TestOuput(self)

  def run_all_tests(self):
    for test in self.__tests.values():
      self.run_test(test)

  def run_test(self, test: IntegrationTest):
    self.__current_test = test
    self.__test_index += 1

    self.__test_output.test_start()

    fly_res = self.__current_test.fly_exec()
    self.__test_output.test_fly_res(fly_res)

    print()

    py_res = self.__current_test.py_exec()
    self.__test_output.test_py_res(py_res)

    if fly_res == py_res:
      self.__test_output.test_success()
    else:
      self.__test_output.test_failure()

    

  def add_test(self, test: IntegrationTest):
    if test.name in self.__tests:
      raise Exception("Duplicate Test")

    self.__tests[test.name] = test

  def get_test(self, name: str):
    return self.__tests.get(name, None)

  def get_current_test(self):
    return self.__current_test

  def get_current_test_index(self):
    return self.__test_index

  def get_nb_tests(self):
    return len(self.__tests)



  

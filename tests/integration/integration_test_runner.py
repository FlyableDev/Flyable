from tests.integration.integration_test import IntegrationTest


class IntegrationTestRunner:
  
  def __init__(self):
    self.__current_test: IntegrationTest | None = None
    self.__tests: dict[str, IntegrationTest] = {}

  def run_all_tests(self):
    for test in self.__tests.values():
      self.run_test(test)

  def run_test(self, test: IntegrationTest):
    self.__current_test = test

    print(f"-------- Running test {self.__current_test.name} --------")

    res = self.__current_test.fly_exec()
    print(f"[Output of test {self.__current_test.name}]")
    print(res)
    print(f"-------- Success running test {self.__current_test.name} --------")

  def add_test(self, test: IntegrationTest):
    if test.name in self.__tests:
      raise Exception("Duplicate Test")

    self.__tests[test.name] = test

  def get_test(self, name: str):
    return self.__tests.get(name, None)



  

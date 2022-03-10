
import os
from tests.integration.integration_test import load_integration_tests
from tests.integration.integration_test_runner import IntegrationTestRunner


def run_tests():
  tests = load_integration_tests(os.path.abspath(os.getcwd()))
  test_runner = IntegrationTestRunner()
  for test in tests:
    test_runner.add_test(test)

  test_runner.run_all_tests()
  

if __name__ == "__main__":
  run_tests()
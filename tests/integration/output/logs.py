
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from tests.integration.integration_test import IntegrationTest

def create_log(test: IntegrationTest):
  with open(f"{test.dir_path}/output/logs.txt", 'w+') as f:
    f.write(f"Logs of test {test.name}")

def add_log(test: IntegrationTest, text: str):
  with open(f"{test.dir_path}/output/logs.txt", 'a') as f:
    f.write(text)
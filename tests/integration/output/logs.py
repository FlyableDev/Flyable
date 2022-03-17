
from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from tests.integration.integration_test import IntegrationTest

def create_log(test: IntegrationTest):
  with open(f"{test.dir_path}/output/logs.txt", 'w+') as f:
    f.write(f"Logs of test {test.name} \n\n")

def add_log(test: IntegrationTest, text: str):
  with open(f"{test.dir_path}/output/logs.txt", 'a') as f:
    f.write(f'[{datetime.now().strftime("%H:%M:%S")}] {text}\n')
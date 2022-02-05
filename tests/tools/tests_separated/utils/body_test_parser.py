from dataclasses import dataclass, field
from os import path
import re
from typing import Literal, TypeAlias, Optional, Callable

from tests.tools.tests_separated.utils.utils import (
    TAG_START,
    TAGS,
    BodyTestState,
    BodyTest,
    FLY_TEST_INFOS,
)


@dataclass
class BodyTestParser:
    file_name: str
    current_state: BodyTestState = BodyTestState.None_
    parsed_tests: list[BodyTest] = field(default_factory=list)

    @property
    def current_test(self):
        return self.parsed_tests[-1]

    def change_state(self, tag: str, tag_arg: list[str]):
        if tag not in TAGS:
            raise NameError(f"Invalid tag ({tag}) for FlyTest")
        self.current_state = TAGS[tag](tag_arg, self)

    def parse_line(self, line: str):
        if self.current_state is BodyTestState.None_:
            return

        elif self.current_state is BodyTestState.New:
            self.parsed_tests.append(BodyTest(self.file_name))
            self.current_state = BodyTestState.Infos

        elif self.current_state is BodyTestState.End:
            self.current_state = BodyTestState.None_

        elif self.current_state is BodyTestState.Body:
            self.current_test.lines.append(line)

        elif self.current_state is BodyTestState.Infos:
            if not line or line.strip() == '"""':
                return
            info_name, info_content = line.split(":", 1)
            info_name = info_name.strip()
            info_content = info_content.strip()
            if info_name not in FLY_TEST_INFOS:
                raise NameError(f"Invalid info flag ({info_name}) for FlyTest")
            self.current_test.infos[info_name] = info_content


def parse_body_test_file(file_path: str):
    test_parser = BodyTestParser(path.basename(file_path))

    with open(file_path, "r") as f:
        lines = f.readlines()

    for line in lines:
        if re.match(TAG_START, line):
            tag, *tag_arg = line.split(":", 1)[1].strip().split(" ")
            if tag not in TAGS:
                raise NameError(f"Invalid tag ({tag}) for FlyTest")
            test_parser.change_state(tag, tag_arg)
            continue
        test_parser.parse_line(line)

    for test in test_parser.parsed_tests:
        test.is_valid_or_raise()

    return {test.name: test for test in test_parser.parsed_tests}

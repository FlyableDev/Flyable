from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from tests.quail.quail_test import QuailTest
from tests.quail.tags.quail_tag import QuailTag, QuailTagType

_QUAIL_VALID_INFOS: list[str] = ["Name", "Flyable-version", "Description"]


class QuailTestState(Enum):
    New = auto()
    Infos = auto()
    Start = auto()
    Body = auto()
    None_ = auto()


@dataclass
class QuailTestParser:
    file_name: str
    current_state: QuailTestState = QuailTestState.None_
    parsed_tests: list[QuailTest] = field(default_factory=list)
    current_value: Any = None

    @property
    def current_test(self):
        return self.parsed_tests[-1]

    def parse_line(self, line: str):
        if QuailTag.get_tag_match(line, QuailTagType.TEST):
            self.__change_state(line)

        match self.current_state:  # type: ignore
            case QuailTestState.None_:
                return
            case QuailTestState.New:
                self.__new_quail_test()
            case QuailTestState.Start:
                self.current_state = QuailTestState.Body
                return
            case QuailTestState.Body:
                self.__add_line_to_current_quail_test(line)
            case QuailTestState.Infos:
                self.__add_info_to_current_quail_test(line)

    def __new_quail_test(self):
        self.parsed_tests.append(
            QuailTest(self.file_name)
            if self.current_value is None
            # here, current_value is the test mode
            else QuailTest(self.file_name, self.current_value)
        )
        self.current_state = QuailTestState.Infos

    def __change_state(self, line: str):
        if not QuailTag.tag_exists(line, QuailTagType.TEST):
            raise NameError(f"Invalid tag ({line}) for QuailTest")
        self.current_state, self.current_value = QuailTag.apply_first_match(
            self, line, QuailTagType.TEST
        )

    def __add_line_to_current_quail_test(self, line: str):
        self.current_test.original_lines.append(line)
        if not QuailTag.get_tag_match(line, QuailTagType.ASSERT):
            self.current_test.lines.append(line)
            return

        line = QuailTag.apply_first_match(self, line, QuailTagType.ASSERT)
        self.current_test.lines.append(line)

    def __add_info_to_current_quail_test(self, line):
        if not line.strip() or line.strip() in ('"""', "'''"):
            return
        info_name, info_content = line.split(":", 1)
        info_name = info_name.strip()
        info_content = info_content.strip()
        if info_name not in _QUAIL_VALID_INFOS:
            raise NameError(f"Invalid info flag ({info_name}) for QuailTest")
        self.current_test.infos[info_name] = info_content

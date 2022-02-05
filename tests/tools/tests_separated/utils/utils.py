from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.tools.tests_separated.utils.body_test_parser import BodyTestParser

from dataclasses import dataclass, field
from typing import Optional, Callable


@dataclass
class StdOut:
    content: str = ""
    write_calls: int = 0


class BodyTestState(Enum):
    New = auto()
    Infos = auto()
    Body = auto()
    End = auto()
    None_ = auto()


@dataclass
class BodyTest:
    file_name: str
    infos: dict[str, str] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def is_valid_or_raise(self):
        if "Name" not in self.infos:
            raise AttributeError("Each test must have a Name")

    def py_compile(self):
        return compile("".join(self.lines), self.file_name, "exec")

    @property
    def name(self):
        return self.infos["Name"]


# ********************** tag functions **********************
def tag_new(args: list[str], test: BodyTestParser) -> BodyTestState:
    if test.current_state is not BodyTestState.None_:
        raise ValueError("You must end a test before starting a new one")
    return BodyTestState.New


def tag_start(args: list[str], test: BodyTestParser) -> BodyTestState:
    if test.current_state is BodyTestState.None_:
        raise ValueError("You must create a test before defining its body")
    return BodyTestState.Body


def tag_end(args: list[str], test: BodyTestParser) -> BodyTestState:
    if test.current_state is not BodyTestState.Body:
        raise ValueError("You must create a test before defining its body")
    return BodyTestState.End


TAGS: dict[str, Callable[[list[str], BodyTestParser], BodyTestState]] = {
    "new": tag_new,
    "start": tag_start,
    "end": tag_end,
}
TAG_START = r" *# *Flytest:\w+.*"
FLY_TEST_INFOS: list[str] = ["Name", "Flyable-version", "Description"]

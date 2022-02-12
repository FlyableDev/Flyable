from __future__ import annotations
from typing import TYPE_CHECKING

from tests.quail.tags.quail_tag import QuailTag, QuailTagType
from tests.quail.utils.trim import trim

if TYPE_CHECKING:
    from tests.quail.parser.quail_test_parser import QuailTestParser, QuailTestState

import re
from typing import Any
import tests.quail.parser.quail_test_parser as quailtest


def load():
    QuailTag(tag_name="new", quail_tag_type=QuailTagType.TEST, apply=tag_new)
    QuailTag(tag_name="start", quail_tag_type=QuailTagType.TEST, apply=tag_start)
    QuailTag(tag_name="end", quail_tag_type=QuailTagType.TEST, apply=tag_end)

    QuailTag(tag_name="-", quail_tag_type=QuailTagType.ASSERT, apply=assert_tag_empty)
    QuailTag(
        tag_name="raises", quail_tag_type=QuailTagType.ASSERT, apply=assert_tag_raises
    )
    QuailTag(tag_name="eq", quail_tag_type=QuailTagType.ASSERT, apply=assert_tag_eq)
    QuailTag(tag_name="==", quail_tag_type=QuailTagType.ASSERT, apply=assert_tag_eq)
    QuailTag(
        tag_name="True", quail_tag_type=QuailTagType.ASSERT, apply=assert_tag_eq_True
    )
    QuailTag(
        tag_name="False", quail_tag_type=QuailTagType.ASSERT, apply=assert_tag_eq_False
    )


# ********************** start test tag functions **********************


def tag_new(match: re.Match, test: QuailTestParser) -> tuple[QuailTestState, Any]:
    if test.current_state is not quailtest.QuailTestState.None_:
        raise ValueError("You must end a test before starting a new one")

    args = match.group(5).strip().split()
    if len(args) > 1:
        raise AttributeError(
            f"Too many arguments passed to the tag new (passed {len(args)})"
        )

    result = None
    if args:
        if args[0] in ("compile", "runtime", "both"):
            result = args[0]
        else:
            raise NameError(f"Unknown argument for the new tag ({args[0]})")
    return quailtest.QuailTestState.New, result


def tag_start(match: re.Match, test: QuailTestParser) -> tuple[QuailTestState, Any]:
    if test.current_state is quailtest.QuailTestState.None_:
        raise ValueError("You must create a test before defining its body")

    args = match.group(5).strip().split()
    if args:
        raise AttributeError(
            f"Too many arguments passed to the tag new (passed {len(args)})"
        )
    return quailtest.QuailTestState.Body, None


def tag_end(match: re.Match, test: QuailTestParser) -> tuple[QuailTestState, Any]:
    if test.current_state is not quailtest.QuailTestState.Body:
        raise ValueError("You must create a test before defining its body")

    args = match.group(5).strip().split()
    if args:
        raise AttributeError(
            f"Too many arguments passed to the tag new (passed {len(args)})"
        )
    return quailtest.QuailTestState.None_, None


# ********************** start test tag functions **********************


# ********************** start assert tag functions **********************


def get_indent(line: str):
    return line[: line.index(line.strip()[0])]


def assert_tag_empty(match: re.Match, test: QuailTestParser) -> str:
    line = match.group(1)
    indent = get_indent(line)
    return indent + f"print(({line.strip()}))\n"


def assert_tag_eq(match: re.Match, test: QuailTestParser) -> str:
    line = match.group(1)
    indent = get_indent(line)
    value = match.group(5).strip()
    return indent + f"print(({line.strip()}) == ({value}))\n"


def assert_tag_eq_True(match: re.Match, test: QuailTestParser) -> str:
    line = match.group(1)
    indent = get_indent(line)
    return indent + f"print(({line.strip()}) == True)\n"


def assert_tag_eq_False(match: re.Match, test: QuailTestParser) -> str:
    line = match.group(1)
    indent = get_indent(line)
    return indent + f"print(({line.strip()}) == False)\n"


def assert_tag_raises(match: re.Match, test: QuailTestParser) -> str:
    line = match.group(1)
    indent = get_indent(line)
    value = match.group(5).strip()

    return (
            trim(
                f"""
                {indent}try:
                {indent}    {line.strip()}
                {indent}except {value or ""}:
                {indent}    print(True)
                {indent}else:
                {indent}    print(False)
                {indent}"""
            )
            + "\n"
    )

# ********************** end assert tag functions **********************

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Callable, Any, Optional

if TYPE_CHECKING:
    from tests.quail.parser.parser import QuailTestParser

from enum import Enum, auto

# trust me, it works
_QUAIL_TAG = r"(.*?)(# *Quail-)(.*?)(?: *: *)(.*?)(?: +|$)(.*)"
"""Groups:\n
1 -> the line before the quail tag starts\n
2 -> the '# Quail-' part of the tag\n
3 -> the name of the tag type (between the '-' and the ':')\n
4 -> the name of tag (what's after the ':')\n
5 -> the content of the tag (what's after the tag name)\n
"""


class QuailTagType(Enum):
    TEST = auto()
    """
    Type of quail tag found on an otherwise empty line.\n
    Its role is to divide clearly the unit test in different parts by changing the state of the parser
    """

    ASSERT = auto()
    """
    Type of quail tag found at the end of a line containing a python expression.\n 
    It modifies the line to include a test
    """

    @property
    def tag_type(self):
        return self.name.lower()


class QuailTag:
    __quail_tags: dict[QuailTagType, dict[str, QuailTag]] = {
        qtype: {} for qtype in QuailTagType
    }

    @classmethod
    def get_tag_match(
            cls, line: str, quail_tag_type: QuailTagType = None
    ) -> Optional[re.Match]:
        match = re.match(_QUAIL_TAG, line)
        return (
            match
            if match
               and (quail_tag_type is None or match.group(3) == quail_tag_type.tag_type)
            else None
        )

    @classmethod
    def tag_exists(cls, line: str, quail_tag_type: QuailTagType = None) -> bool:
        tag = cls.get_tag_match(line, quail_tag_type)
        if tag is None:
            return False
        tag = tag.group(4)
        if quail_tag_type is None:
            return any(tag in quail_tag for quail_tag in cls.__quail_tags.values())
        return tag in cls.__quail_tags[quail_tag_type]

    @classmethod
    def apply_first_match(
            cls, quail_test_parser: QuailTestParser, line: str, quail_tag_type: QuailTagType
    ):
        quail_tags: list[QuailTag] = [*cls.__quail_tags[quail_tag_type].values()]
        match = cls.get_tag_match(line)
        if not match:
            raise ValueError("Line has no tag")
        for quail_tag in quail_tags:
            if quail_tag.tag_matches(line):
                return quail_tag.apply(match, quail_test_parser)
        raise NameError(
            f"There are no Quail tag named {match.group(4)}) in type {quail_tag_type.name}"
        )

    def __init__(
            self,
            tag_name: str,
            quail_tag_type: QuailTagType,
            apply: Callable[[re.Match, QuailTestParser], Any],
    ):
        self.tag_name = tag_name
        self.quail_tag_type = quail_tag_type
        self.__quail_tags[quail_tag_type][self.tag_name] = self
        self.apply = apply

    def tag_matches(self, line: str):
        match = self.get_tag_match(line)
        return (
                match
                and match.group(3) == self.quail_tag_type.tag_type
                and match.group(4) == self.tag_name
        )


def __load():
    import tests.quail.tags.tags as tags

    tags.load()


__load()

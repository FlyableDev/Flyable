from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Callable, TypeAlias
import json

if TYPE_CHECKING:
    from flyable.code_gen.code_builder import CodeBuilder
    from flyable.code_gen.code_gen import CodeBlock

Tree_dict: TypeAlias = dict[str, list[str | dict]]


class BranchViewer:
    """Class to see the code branches"""

    def __init__(self, builder: CodeBuilder) -> None:
        self.__builder = builder
        self.tree: Tree_dict = {}
        self.__paths: dict[str, list] = {}
        self.__setup()

    def __str__(self) -> str:
        return json.dumps(self.__paths, indent=4)

    def __setup(self):
        """Modifies builder to register when branches are created"""
        self.__builder.set_insert_block = self.__new_set_insert_block(
            self.__builder.set_insert_block
        )
        self.__builder.br = self.__new_br(self.__builder.br)
        self.__builder.cond_br = self.__new_cond_br(self.__builder.cond_br)

    def __new_set_insert_block(self, set_insert_block: Callable):
        @wraps(set_insert_block)
        def wrapper(block: CodeBlock):
            block_key = self.__format_block(block)
            if block_key not in self.__paths:
                self.tree[block_key] = []
                self.__paths[block_key] = self.tree[block_key]
            return set_insert_block(block)

        return wrapper

    def __new_br(self, br: Callable):
        @wraps(br)
        def wrapper(block: CodeBlock):
            current_block = self.__builder.get_current_block()
            key = self.__format_block(current_block)
            block_key = self.__format_block(block)
            ls = []
            self.__paths[key].append({block_key: ls})
            self.__make_path(block_key, ls)
            return br(block)

        return wrapper

    def __new_cond_br(self, cond_br: Callable):
        @wraps(cond_br)
        def wrapper(value: int, block_true: CodeBlock, block_false: CodeBlock):
            current_block = self.__builder.get_current_block()
            key = self.__format_block(current_block)
            block_true_key = self.__format_block(block_true)
            block_false_key = self.__format_block(block_false)
            ls_true = []
            ls_false = []

            self.__paths[key].append(
                {"True": {block_true_key: ls_true}, "False": {block_false_key: ls_false}}
            )
            self.__make_path(block_true_key, ls_true)
            self.__make_path(block_false_key, ls_false)

            return cond_br(value, block_true, block_false)

        return wrapper

    def __make_path(self, block_name: str, ref: list):
        self.__paths[block_name] = ref

    def __format_block(self, block: CodeBlock):
        return f"{block.get_name()}"

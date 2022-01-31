from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Callable, TypeAlias, Optional
import json

if TYPE_CHECKING:
    from flyable.code_gen.code_builder import CodeBuilder
    from flyable.code_gen.code_gen import CodeBlock

from flyable.debug.utils import *
from flyable.debug.debug_flags_list import *

Tree_dict: TypeAlias = dict[str, list[str | dict]]


class BranchViewer:
    """Class to see the code branches"""

    def __init__(self, builder: CodeBuilder) -> None:
        self.__builder = builder
        self.__defined_blocks: list[CodeBlock] = []
        self.__current_block: Optional[CodeBlock] = None
        self.__setup()

    def show_tree(self):
        def show_branches(branches: list[CodeBlock]):
            if not branches:
                return
            for branch in branches:
                dprint(f"|-> {branch}")

        for block in self.__defined_blocks:
            dprint(f"{block}:")
            dindent_plus()
            show_branches(block.get_br_blocks())
            dindent_minus()

    def clear(self):
        self.__defined_blocks.clear()
        ddivider(divider_length=30, indent=0)
        dprint("[RESETING BLOCKS]", indent=0)
        ddivider(divider_length=30, indent=0)

    def __setup(self):
        """Modifies builder to register when branches are created"""
        self.__builder.set_insert_block = self.__new_set_insert_block(
            self.__builder.set_insert_block
        )
        self.__builder.br = self.__new_br(self.__builder.br)
        self.__builder.cond_br = self.__new_cond_br(self.__builder.cond_br)
        self.__builder.create_block = self.__new_create_block(
            self.__builder.create_block
        )

    def __new_create_block(self, create_block: Callable):
        @wraps(create_block)
        def wrapper(label: str = None):
            block = create_block(label)
            if FLAG_SHOW_BLOCK_BRANCHES.value == "all":
                dprint(f"\t|> Creating {block}")
            return block

        return wrapper

    def __new_set_insert_block(self, set_insert_block: Callable):
        @wraps(set_insert_block)
        def wrapper(block: CodeBlock):
            prev_block = self.__builder.get_current_block()
            msg: str
            if block in self.__defined_blocks:
                if prev_block.get_id() != 0:  # type: ignore
                    dprint(
                        f"Going back to {block}"
                        if block.get_id() != 0
                        else f"\t|> Allocating memory in {block}"
                    )
            else:
                dprint(f"Defining block {block}")
                self.__defined_blocks.append(block)

            self.__current_block = block
            return set_insert_block(block)

        return wrapper

    def __new_br(self, br: Callable):
        @wraps(br)
        def wrapper(block: CodeBlock):
            dprint(f"\t|-> {block}")
            return br(block)

        return wrapper

    def __new_cond_br(self, cond_br: Callable):
        @wraps(cond_br)
        def wrapper(value: int, block_true: CodeBlock, block_false: CodeBlock):
            dindent_plus()
            dprint(f"|> if value (id:{value}) is 1")
            dprint(f"\t|-> {block_true}")
            dprint(f"|> else")
            dprint(f"\t|-> {block_false}")
            dindent_minus()
            return cond_br(value, block_true, block_false)

        return wrapper

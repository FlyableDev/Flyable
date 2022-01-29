from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Callable, TypeAlias, Optional
import json

if TYPE_CHECKING:
    from flyable.code_gen.code_builder import CodeBuilder
    from flyable.code_gen.code_gen import CodeBlock

from flyable.debug.utils import dprint, ddivider, dindent_plus, dindent_minus, dset_indent

Tree_dict: TypeAlias = dict[str, list[str | dict]]


class BranchViewer:
    """Class to see the code branches"""

    def __init__(self, builder: CodeBuilder) -> None:
        self.__builder = builder
        self.__defined_blocks: list[CodeBlock] = []
        self.__current_block: Optional[CodeBlock] = None
        self.__current_block_tree = {}
        self.__setup()

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
            dset_indent(0)
            self.__current_block = block
            msg = ""
            if block in self.__defined_blocks:
                msg = f"Going back to {block}"
            else:
                msg = f"Defining block {block}"
                self.__defined_blocks.append(block)

            dprint(msg)
            dindent_plus()
            return set_insert_block(block)

        return wrapper

    def __new_br(self, br: Callable):
        @wraps(br)
        def wrapper(block: CodeBlock):
            dprint(f"|-> {block}")
            return br(block)

        return wrapper

    def __new_cond_br(self, cond_br: Callable):
        @wraps(cond_br)
        def wrapper(value: int, block_true: CodeBlock, block_false: CodeBlock):
            dprint(f"|> if value (id:{value})")
            dprint(f"\t|-> {block_true}")
            dprint(f"|> else")
            dprint(f"\t|-> {block_false}")
            return cond_br(value, block_true, block_false)

        return wrapper

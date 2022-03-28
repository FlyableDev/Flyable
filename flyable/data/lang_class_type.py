from __future__ import annotations
from typing import TYPE_CHECKING
import flyable.code_gen.ref_counter as ref_counter
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen
import flyable.code_gen.code_builder as code_builder
import flyable.code_gen.runtime as runtime
import flyable.code_gen.caller as caller
import flyable.code_gen.code_gen as _gen

if TYPE_CHECKING:
    from flyable.code_gen.code_gen import CodeGen
    from flyable.data.lang_class import LangClass


class LangClassType:
    """
    Class containing all of the relevant functions that need to be generated for a Python type definition
    """

    def __init__(self, _class: LangClass):
        self.__lang_class = _class

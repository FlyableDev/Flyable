from __future__ import annotations

import ast
from typing import TYPE_CHECKING
from flyable.data.lang_type import LangType
import flyable.data.lang_class_type as class_type

if TYPE_CHECKING:
    from flyable.data.lang_file import LangFile
    from flyable.data.lang_func import LangFunc
    from flyable.code_gen.code_gen import StructType
    from flyable.data.attribute import Attribut


class LangClass:

    def __init__(self, node: ast.ClassDef):
        self.__node: ast.ClassDef = node
        self.__funcs: list[LangFunc] = []
        self.__attributes: list[Attribut] = []
        self.__id: int = -1
        self.__struct: StructType | None = None
        self.__file: LangFile | None = None
        self.__inherits: list[LangClass] = []
        self.__class_type = class_type.LangClassType(self)

    def get_node(self):
        return self.__node

    def set_file(self, file: LangFile):
        self.__file = file

    def get_file(self):
        return self.__file

    def add_func(self, func: LangFunc):
        func.set_class(self)
        func.set_id(len(self.__funcs))
        self.__funcs.append(func)

    def get_func(self, index: int | str):
        if isinstance(index, int):
            return self.__funcs[index]
        for func in self.__funcs:
            if func.get_name() == index:
                return func
        return None

    def get_funcs_count(self):
        return len(self.__funcs)

    def funcs_iter(self):
        return iter(self.__funcs)

    def set_id(self, id: int):
        self.__id = id

    def get_id(self):
        return self.__id

    def get_name(self) -> str:
        return self.__node.name

    def get_full_name(self):
        if self.__file is None:
            raise NotImplementedError(f"LangClass {self.get_name()} is not in any file")
        return self.__file.get_path() + self.get_name()

    def add_attribute(self, attr: Attribut):
        attr.set_id(len(self.__attributes))
        self.__attributes.append(attr)

    def get_attribute(self, index: int | str):
        if isinstance(index, int):
            return self.__attributes[index]
        for attribute in self.__attributes:
            if attribute.get_name() == index:
                return attribute
        return None

    def get_attributes_count(self):
        return len(self.__attributes)

    def attributes_iter(self):
        return iter(self.__attributes)

    def add_inherit(self, inherit: LangClass):
        self.__inherits.append(inherit)

    def iter_inherits(self):
        return iter(self.__inherits)

    def get_inherits(self, index: int):
        return self.__inherits[index]

    def set_struct(self, struct: StructType):
        self.__struct = struct

    def get_struct(self):
        if self.__struct is None:
            raise Exception(f"Class {self.get_full_name()} has no structure.")
        return self.__struct

    def get_lang_type(self):
        return LangType(LangType.Type.OBJECT, self.__id)

    def get_class_type(self):
        return self.__class_type

    def clear_info(self):
        self.__class_type = class_type.LangClassType(self)
        for func in self.__funcs:
            func.clear_info()

    def get_qualified_name(self):
        if self.__inherits: 
            return f"{str.join('.', reversed(self.__inherits))}.{self.get_name()}"
        return self.get_name()        

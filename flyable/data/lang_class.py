from typing import Union, List
from flyable.data.lang_file import LangFile
from flyable.data.lang_func import LangFunc
from flyable.data.lang_type import LangType
import flyable.data.lang_class_type as class_type


class LangClass:

    def __init__(self, node):
        self.__node = node
        self.__funcs: List[LangFunc] = []
        self.__attributes = []
        self.__id: int = -1
        self.__struct = None
        self.__file: Union[LangFile, None] = None
        self.__inherits = []
        self.__class_type = class_type.LangClassType(self)

    def get_node(self):
        return self.__node

    def set_file(self, file):
        self.__file = file

    def get_file(self):
        return self.__file

    def add_func(self, func):
        func.set_class(self)
        func.set_id(len(self.__funcs))
        self.__funcs.append(func)

    def get_func(self, index):
        if isinstance(index, int):
            return self.__funcs[index]
        else:
            for e in self.__funcs:
                if e.get_name() == index:
                    return e

    def funcs_iter(self):
        return iter(self.__funcs)

    def set_id(self, id: int):
        self.__id = id

    def get_id(self):
        return self.__id

    def get_name(self) -> str:
        return self.__node.name

    def get_full_name(self):
        return self.__file.get_path() + self.get_name()

    def add_attribute(self, attr):
        attr.set_id(len(self.__attributes))
        self.__attributes.append(attr)

    def get_attribute(self, index):
        if isinstance(index, int):
            return self.__attributes[index]
        elif isinstance(index, str):
            for e in self.__attributes:
                if e.get_name() == index:
                    return e
        return None

    def get_attributes_count(self):
        return len(self.__attributes)

    def attributes_iter(self):
        return iter(self.__attributes)

    def add_inherit(self, inherit):
        self.__inherits.append(inherit)

    def iter_inherits(self):
        return iter(self.__inherits)

    def get_inherits(self, index: int):
        return self.__inherits[index]

    def set_struct(self, struct):
        self.__struct = struct

    def get_struct(self):
        return self.__struct

    def get_lang_type(self):
        return LangType(LangType.Type.OBJECT, self.__id)

    def get_class_type(self):
        return self.__class_type

    def clear_info(self):
        self.__class_type = class_type.LangClassType(self)
        for func in self.__funcs:
            func.clear_info()

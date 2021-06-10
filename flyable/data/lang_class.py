from flyable.data.lang_type import LangType


class LangClass:

    def __init__(self, node):
        self.__node = node
        self.__funcs = []
        self.__attributs = []
        self.__id = -1
        self.__struct = None
        self.__file = None

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

    def set_id(self, id):
        self.__id = id

    def get_id(self):
        return self.__id

    def get_name(self):
        return self.__node.name

    def add_attribut(self, attr):
        attr.set_id(len(self.__attributs))
        self.__attributs.append(attr)

    def get_attribut(self, index):
        if isinstance(index, int):
            return self.__attributs[index]
        elif isinstance(index, str):
            for e in self.__attributs:
                if e.get_name() == index:
                    return e
        return None

    def get_attributs_count(self):
        return len(self.__attributs)

    def attributs_iter(self):
        return iter(self.__attributs)

    def set_struct(self, struct):
        self.__struct = struct

    def get_struct(self):
        return self.__struct

    def get_lang_type(self):
        return LangType(LangType.Type.OBJECT, self.__id)

import os
from typing import Any, AnyStr


class LangFile:
    """
    Representation of a Python textual file. In Python it represents a module
    """

    def __init__(self, path: str = "", txt: str = ""):
        self.__path: str = path
        self.__text: str = txt
        self.__classes: list = []
        self.__funcs: list = []
        self.__global_func = None
        self.__ast = None

    def read_from_path(self, path: str):
        with open(path) as f:
            self.__path = os.path.abspath(path)
            self.__text = f.read()

    def find_content(self, name):
        """
        Looks the list of classes and functions to return the first on met with the correct name.
        """
        for e in self.__funcs:
            if e.get_name() == name:
                return e
        for e in self.__classes:
            if e.get_name() == name:
                return e
        return None

    def clear_info(self):
        for e in self.__classes:
            e.clear_info()
        for e in self.__funcs:
            e.clear_info()

        if self.__global_func is not None:
            self.__global_func.clear_info()

    def add_class(self, _class):
        _class.set_file(self)
        self.__classes.append(_class)

    def get_class(self, index):
        return self.__classes[index]

    def get_classes_count(self):
        return len(self.__classes)

    def add_func(self, func):
        func.set_file(self)
        self.__funcs.append(func)

    def get_func(self, index):
        return self.__funcs[index]

    def set_global_func(self, global_func):
        self.__global_func = global_func

    def get_global_func(self):
        return self.__global_func

    def get_funcs_count(self):
        return len(self.__funcs)

    def get_path(self):
        return self.__path

    def get_text(self):
        return self.__text

    def set_ast(self, ast):
        self.__ast = ast

    def get_ast(self):
        return self.__ast

import os


class LangFile:
    """
    Representation of a Python textual file. In Python it represents a module
    """

    def __init__(self, path="", txt=""):
        self.__path = path
        self.__text = txt
        self.__classes = []
        self.__funcs = []

    def read_from_path(self, path):
        with open(path) as f:
            self.__path = os.path.abspath(path)
            self.__text = str(f.read())

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

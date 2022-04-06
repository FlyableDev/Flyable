from __future__ import annotations

import os
from typing import Union
import flyable.data.lang_func as lang_func


class LangFile:
    """
    Representation of a Python textual file. In Python it represents a module
    """

    def __init__(self, path: str = "", txt: str = ""):
        self.__path: str = path
        self.__text: str = txt
        self.__funcs = []

    def read_from_path(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            self.__path = os.path.abspath(path)
            self.__text = f.read()

    def find_content_by_name(self, name: str) -> Union[lang_func.LangFunc, None]:
        """
        Looks at the list of functions to return the first with a matching name.
        If no match was found, looks at the list of classes to return the first with a matching name.
        If there is no match again, returns None

        Args:
            name (str): the name of the content we want to find

        Returns:
            the function or the class with the matching name or None if none was found
        """
        funcs_and_classes: list[lang_func.LangFunc] = [*self.__funcs, *self.__classes]
        for e in funcs_and_classes:
            if e.get_name() == name:
                return e
        return None

    def find_content_by_id(self, id: int) -> Union[lang_func.LangFunc, None]:
        """
        Looks at the list of functions to return the first with a matching id.
        If no match was found, looks at the list of classes to return the first with a matching id.
        If there is no match again, returns None

        Args:
            id (int): the id of the content we want to find

        Returns:
            the function or the class with the matching id or None if none was found
        """
        funcs_and_classes: list[lang_func.LangFunc] = [*self.__funcs, *self.__classes]
        for e in funcs_and_classes:
            if e.get_id() == id:
                return e
        return None

    def add_class(self, _class):
        _class.set_file(self)
        self.__classes.append(_class)

    def get_class(self, index: int):
        return self.__classes[index]

    def get_classes_count(self):
        return len(self.__classes)

    def add_func(self, func: lang_func.LangFunc):
        func.set_file(self)
        self.__funcs.append(func)

    def get_func(self, index: int):
        return self.__funcs[index]

    def get_funcs_count(self):
        return len(self.__funcs)

    def funcs_iter(self):
        return iter(self.__funcs)

    def get_qualified_name(self):
        return ""

    def get_path(self):
        return self.__path

    def get_text(self):
        return self.__text

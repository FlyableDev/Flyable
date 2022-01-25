from __future__ import annotations

import os
from typing import Union, List
from ast import Module

import flyable.data.lang_func as lang_func
import flyable.data.lang_class as lang_class


class LangFile:
    """
    Representation of a Python textual file. In Python it represents a module
    """

    def __init__(self, path: str = "", txt: str = ""):
        self.__path: str = path
        self.__text: str = txt
        self.__classes: List[lang_class.LangClass] = []
        self.__funcs: List[lang_func.LangFunc] = []
        self.__global_func = None
        self.__ast: Union[Module, None] = None

    def read_from_path(self, path: str):
        with open(path) as f:
            self.__path = os.path.abspath(path)
            self.__text = f.read()

    def find_content_by_name(self, name: str) -> Union[lang_func.LangFunc, lang_class.LangClass, None]:
        """
        Looks at the list of functions to return the first with a matching name.
        If no match was found, looks at the list of classes to return the first with a matching name.
        If there is no match again, returns None

        Args:
            name (str): the name of the content we want to find

        Returns:
            the function or the class with the matching name or None if none was found
        """
        funcs_and_classes: list[lang_func.LangFunc | lang_class.LangClass] = [*self.__funcs, *self.__classes]
        for e in funcs_and_classes:
            if e.get_name() == name:
                return e
        return None

    def find_content_by_id(self, id: int) -> Union[lang_func.LangFunc, lang_class.LangClass, None]:
        """
        Looks at the list of functions to return the first with a matching id.
        If no match was found, looks at the list of classes to return the first with a matching id.
        If there is no match again, returns None

        Args:
            id (int): the id of the content we want to find

        Returns:
            the function or the class with the matching id or None if none was found
        """
        funcs_and_classes: list[lang_func.LangFunc | lang_class.LangClass] = [*self.__funcs, *self.__classes]
        for e in funcs_and_classes:
            if e.get_id() == id:
                return e
        return None

    def clear_info(self):
        """
        Calls `clear_info()` on all the classes contained in the list of classes and 
        on all the functions contained in the list of functions.

        Also, it calls `clear_info()` on the global function if there is one
        """
        funcs_and_classes: list[lang_func.LangFunc | lang_class.LangClass] = [*self.__funcs, *self.__classes]
        for e in funcs_and_classes:
            e.clear_info()

        if self.__global_func is not None:
            self.__global_func.clear_info()

    def add_class(self, _class: lang_class.LangClass):
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

    def set_global_func(self, global_func: lang_func.LangFunc):
        self.__global_func = global_func

    def get_global_func(self):
        return self.__global_func

    def get_funcs_count(self):
        return len(self.__funcs)

    def get_path(self):
        return self.__path

    def get_text(self):
        return self.__text

    def set_ast(self, ast: Module):
        self.__ast = ast

    def get_ast(self):
        return self.__ast

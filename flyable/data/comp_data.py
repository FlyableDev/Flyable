import collections
from typing import Any, Union, List, Dict

from flyable.data.lang_file import LangFile
from flyable.data.lang_func import LangFunc


class CompData:
    """
    Class that holds all the structures found during the compiling process
    """

    def __init__(self):
        self.__files: Dict[str, LangFile] = collections.OrderedDict()
        self.__configs: Dict[str, Any] = {}
        self.__current_iter: int = 0

    def add_file(self, file: LangFile):
        self.__files[file.get_path()] = file

    def get_file(self, index):
        if isinstance(index, str):  # get item by path
            return self.__files.get(index)
        elif isinstance(index, int):  # get item by index
            return list(self.__files.values())[index]

    def get_file_by_path(self, path: str) -> Union[LangFile, None]:
        """Get the file at the specified path

        Args:
            path (str): the path of the file

        Returns:
            Union[LangFile, None]: The file with a matching path, or None if there isn't one
        """
        return self.__files.get(path)

    def get_files_count(self):
        return len(self.__files)

    def files_iter(self):
        return iter(self.__files.values())

    def add_func(self, func: LangFunc):
        func.set_id(self.get_funcs_count())
        self.__funcs.append(func)

    def get_func(self, index: int):
        return self.__funcs[index]

    def get_funcs_count(self):
        return len(self.__funcs)

    def funcs_iter(self):
        return iter(self.__funcs)

    def set_config(self, name: str, data: Any):
        self.__configs[name] = data

    def get_config(self, name: str):
        return self.__configs[name]

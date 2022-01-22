import collections
from typing import Any, Union, List, Dict
from flyable.data.lang_class import LangClass

from flyable.data.lang_file import LangFile
from flyable.data.lang_func import LangFunc


class CompData:
    """
    Class that holds all the structures found during the compiling process
    """

    def __init__(self):
        self.__files: Dict[str, LangFile] = collections.OrderedDict()
        self.__funcs: List[LangFunc] = []
        self.__classes: List[LangClass] = []
        self.__configs: Dict[str, Any] = {}
        self.__change: bool = False
        self.__current_iter: int = 0

    def clear_info(self):
        """
        Clear info ask to every data he holds to remove parsed defined data
        """
        for e in list(self.__files.values()) + self.__funcs + self.__classes: # type: ignore
            e.clear_info()

    def add_file(self, file: LangFile):
        self.__change = True
        self.__files[file.get_path()] = file

    def get_file(self, index: Union[str, int]) -> Union[LangFile, None]:
        """
        Deprecated: 
            you should call `get_file_by_idx` or `get_file_by_path` instead
        """
        if isinstance(index, str):  # get item by path
            return self.__files.get(index)
        elif isinstance(index, int):  # get item by index
            return list(self.__files.values())[index]

    def get_file_by_index(self, idx: int) -> Union[LangFile, None]:
        """Get the file at the specified index

        Args:
            idx (int): the index of the file in the file dict

        Returns:
            Union[LangFile, None]: The file at specified index, or None if the index is not in bound
        """
        # the `- 1` in `abs(idx) - 1` is necessary because if we have a list of length n and want
        # to access the 0th element with negative idx, it will be index -n but the abs(-n) == n
        # and it wouldn't pass the test abs(idx) < len(list) if one wasn't substracted from it
        return list(self.__files.values())[idx] if abs(idx) - 1 < len(self.__files.values()) else None

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

    def add_func(self, func: LangFunc):
        self.__change = True
        func.set_id(self.get_funcs_count())
        self.__funcs.append(func)

    def get_func(self, index: int):
        return self.__funcs[index]

    def get_funcs_count(self):
        return len(self.__funcs)

    def funcs_iter(self):
        return iter(self.__funcs)

    def add_class(self, _class: LangClass):
        self.__change = True
        _class.set_id(self.get_classes_count())
        self.__classes.append(_class)

    def get_class(self, index: int):
        return self.__classes[index]

    def get_classes_count(self):
        return len(self.__classes)

    def classes_iter(self):
        return iter(self.__classes)

    def set_config(self, name: str, data: Any):
        self.__configs[name] = data

    def get_config(self, name: str):
        return self.__configs[name]

    def set_changed(self, change: bool):
        self.__change = change

    def is_changed(self):
        return self.__change

    def increment_current_iteration(self):
        self.__current_iter += 1

    def get_current_iter(self):
        return self.__current_iter

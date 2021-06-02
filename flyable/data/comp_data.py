import collections


class CompData:
    """
    Class that holds all the structures found during the compiling process
    """

    def __init__(self):
        self.__files = collections.OrderedDict()
        self.__funcs = []
        self.__classes = []

    def add_file(self, file):
        self.__files[file.get_path()] = file

    def get_file(self, index):
        if isinstance(index, str):  # get item by path
            return self.__files[index]
        elif isinstance(index, int):  # get item by index
            return list(self.__files.items())[index][1]

    def get_files_count(self):
        return len(self.__files)

    def add_func(self, func):
        func.set_id(self.get_funcs_count())
        self.__funcs.append(func)

    def get_func(self, index):
        return self.__funcs[index]

    def get_funcs_count(self):
        return len(self.__funcs)

    def funcs_iter(self):
        return iter(self.__funcs)

    def add_class(self, _class):
        _class.set_id(self.get_classes_count())
        self.__classes.append(_class)

    def get_class(self, index):
        return self.__classes[index]

    def get_classes_count(self):
        return len(self.__classes)

    def classes_iter(self):
        return iter(self.__classes)

    def find_main(self):
        for e in self.funcs_iter():
            if e.get_name() == "main":
                if e.get_args_count() == 0:
                    return e
        return None

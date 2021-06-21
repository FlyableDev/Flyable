import collections


class CompData:
    """
    Class that holds all the structures found during the compiling process
    """
    def __init__(self):
        self.__files = collections.OrderedDict()
        self.__funcs = []
        self.__classes = []
        self.__configs = {}
        self.__change = False

    def clear_info(self):
        """
        Clear info ask to every data he holds to remove parsed defined data
        """
        for e in self.__funcs:
            e.clear_info()
        for e in self.__classes:
            e.clear_info()

    def add_file(self, file):
        self.__change = True
        self.__files[file.get_path()] = file

    def get_file(self, index):
        if isinstance(index, str):  # get item by path
            return self.__files[index]
        elif isinstance(index, int):  # get item by index
            return list(self.__files.items())[index][1]

    def get_files_count(self):
        return len(self.__files)

    def add_func(self, func):
        self.__change = True
        func.set_id(self.get_funcs_count())
        self.__funcs.append(func)

    def get_func(self, index):
        return self.__funcs[index]

    def get_funcs_count(self):
        return len(self.__funcs)

    def funcs_iter(self):
        return iter(self.__funcs)

    def add_class(self, _class):
        self.__change = True
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

    def set_config(self, name, data):
        self.__configs[name] = data

    def get_config(self, name):
        return self.__configs[name]

    def set_changed(self, change):
        self.__change = change

    def is_changed(self):
        return self.__change

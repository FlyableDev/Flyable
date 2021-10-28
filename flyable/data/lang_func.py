import ast

from flyable.data.lang_func_impl import LangFuncImpl
import flyable.data.lang_type as type


class LangFunc:
    """
    Represents a class definition
    Ex:
    def my_func(a,b):
        body....
    """

    def __init__(self, node):

        self.__node = node

        self.__id = -1
        # Setup args
        self.__setup_unknown_impl()

        self.__class_lang = None
        self.__file = None
        self.__is_global = False

    def set_class(self, _class):
        self.__class_lang = _class

    def get_class(self):
        return self.__class_lang

    def set_id(self, id):
        self.__id = id

    def get_id(self):
        return self.__id

    def add_impl(self, func):
        func.set_parent_func(self)
        func.set_id(len(self.__impls))
        self.__impls.append(func)

    def get_impl(self, index):
        return self.__impls[index]

    def set_file(self, file):
        self.__file = file

    def get_file(self):
        return self.__file

    def get_impls_count(self):
        return len(self.__impls)

    def impls_iter(self):
        return iter(self.__impls)

    def find_impl_by_signature(self, args_type):
        for i in self.__impls:
            if not i.is_unknown() and i.get_args_count() == len(args_type):  # Same arguments count
                same_signature = True
                for j in range(i.get_args_count()):
                    if i.get_arg(j) != args_type[j]:
                        same_signature = False
                if same_signature:
                    return i

    def get_min_args(self):
        """
        Returns the minimal amount of arguments required to call.
        """
        # Amount of total args vs the amount of args with default values
        if isinstance(self.__node, ast.FunctionDef):
            return len(self.__node.args.args) - len(self.__node.args.defaults)
        return 0

    def get_max_args(self):
        """
        Returns the maximum amount that can be used on this function.
        -1 means varargs
        """
        if isinstance(self.__node, ast.FunctionDef):
            return len(self.__node.args.args)
        return 0

    def get_unknown_impl(self):
        return self.__impls[0]

    def get_node(self):
        return self.__node

    def get_name(self):
        if isinstance(self.__node, ast.FunctionDef):
            return self.__node.name
        else:
            return "@global@module@"

    def get_arg(self, index):
        return self.__node.args.args[index]

    def get_args_count(self):
        if isinstance(self.__node, ast.FunctionDef):
            arg_node = self.__node.args
            return len(arg_node.args)
        return 0

    def args_iter(self):
        if isinstance(self.__node, ast.FunctionDef):
            return iter(self.__node.args.args)
        return iter([])

    def set_global(self, _global):
        self.__is_global = _global

    def is_global(self):
        return self.__is_global

    def clear_info(self):
        self.__impls.clear()
        self.__setup_unknown_impl()

    def __setup_unknown_impl(self):
        # Setup args
        self.__impls = [LangFuncImpl()]
        self.__impls[0].set_parent_func(self)
        self.__impls[0].set_unknown(True)
        for e in self.args_iter():
            self.get_unknown_impl().add_arg(type.get_unknown_type())

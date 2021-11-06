import ast
import sys
from flyable.data.comp_data import CompData
import flyable.data.lang_func as func
import flyable.data.lang_class as _class
from flyable.data.error_thrower import ErrorThrower


class PreParser(ast.NodeVisitor, ErrorThrower):
    """
    PreParse visitor is a class that visit all available nodes to find all possibles functions and classes so we can
    supply them to the Code Generator and the
    """

    def __init__(self, comp_data, code_gen):
        super().__init__()
        self.__data = comp_data
        self.__current_class = None
        self.__current_file = None
        self.__code_gen = code_gen

    def parse(self, comp_data: CompData):
        for i in range(comp_data.get_files_count()):
            file = comp_data.get_file(i)
            self.__current_file = file
            # Generate the ast using the CPython ast module
            ast_tree = ast.parse(file.get_text(), filename=file.get_path(), mode='exec', type_comments=False,
                                 feature_version=sys.version_info[0:2])
            #ReprVisitor().visit(ast_tree)
            file.set_ast(ast_tree)
            global_func = func.LangFunc(ast_tree)
            global_func.set_global(True)
            global_func.set_file(file)
            file.set_global_func(global_func)
            self.visit(ast_tree)

    def generic_visit(self, node):
        super().generic_visit(node)

    def visit_FunctionDef(self, node):
        new_func = func.LangFunc(node)
        new_func.set_file(self.__current_file)
        self.__current_file.add_func(new_func)
        if self.__current_class is None:
            self.__data.add_func(new_func)
        else:
            self.__current_class.add_func(new_func)
        super().generic_visit(node)

    def visit_ClassDef(self, node):
        new_class = _class.LangClass(node)
        new_class.set_file(self.__current_file)
        self.__data.add_class(new_class)
        self.__current_file.add_class(new_class)
        self.__current_class = new_class
        super().generic_visit(node)
        self.__current_class = None

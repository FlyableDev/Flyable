class LangClassType:

    """
    Class containing all of the relevant functions that need to be generated for a Python type definition
    """

    def __init__(self):
        self.__traverse_func = None
        self.__get_attr_func = None
        self.__set_attr_func = None
        self.__dealloc_func = None

    def generate(self, code_gen):
        self.__gen_get_attr()
        self.__gen_set_attr()
        self.__gen_traverse()
        self.__gen_dealloc()

    def __gen_traverse(self):
        pass

    def __gen_get_attr(self):
        pass

    def __gen_set_attr(self):
        pass

    def __gen_dealloc(self):
        pass

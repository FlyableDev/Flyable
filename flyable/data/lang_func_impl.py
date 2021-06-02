import flyable.data.lang_type as type
import flyable.parse.context as context


class LangFuncImpl:
    """"
    Represents an actual implementation of a function.
    In most cases a function will generate two different sets of machine instructions.
    This class represent a concrete implementation of this.
    Example :

    def test(a,b): # This is a function definition
        return a + b

    test(10,20) # Generate one implementation of the code to add both int args
    test("a","b") # Generate another implementation of the code that calls __add__ from the str class
    """

    def __init__(self):
        self.__unknown = False
        self.__code_func = None
        self.__args = []
        self.__parent_func = None
        self.__node_infos = {}

        self.__has_parse_started = False
        self.__has_parse_ended = False

        self.__return_type = type.LangType()

        self.__context = context.Context()

        self.__can_raise = False

    def add_arg(self, arg):
        self.__args.append(arg)

    def get_arg(self, index):
        return self.__args[index]

    def get_args_count(self):
        return len(self.__args)

    def args_iter(self):
        return iter(self.__args)

    def set_parent_func(self, parent):
        self.__parent_func = parent

    def get_parent_func(self):
        return self.__parent_func

    def set_unknown(self, unknow):
        self.__unknown = unknow

    def is_unknown(self):
        return self.__unknown

    def is_parse_started(self):
        return self.__has_parse_started

    def is_parse_ended(self):
        return self.__has_parse_ended

    def get_return_type(self):
        return self.__return_type

    def set_return_type(self, return_type):
        self.__return_type = return_type

    def set_code_func(self, func):
        self.__code_func = func

    def get_code_func(self):
        return self.__code_func

    def set_node_info(self, node, info):
        self.__node_infos[id(node)] = info

    def get_node_info(self, node):
        key = id(node)
        if key in self.__node_infos:
            return self.__node_infos[id(node)]
        return None

    def get_context(self):
        return self.__context

    def set_can_raise(self, can_raise):
        """
        Set if the implementation can potentially raise an exception during his execution
        """
        self.__can_raise = can_raise

    def can_raise(self):
        """
        Return if the implementation can potentially raise an exception during his execution
        """
        return self.__can_raise

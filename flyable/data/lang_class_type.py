import flyable.code_gen.ref_counter as ref_counter

class LangClassType:

    """
    Class containing all of the relevant functions that need to be generated for a Python type definition
    """

    def __init__(self):
        self.__type_global_instance = None
        self.__traverse_func = None
        self.__get_attr_func = None
        self.__set_attr_func = None
        self.__dealloc_func = None

    def generate(self, code_gen, builder):

        type_instance = builder.global_var(self.get_type_global_instance())
        type_instance = builder.load(type_instance)
        ref_counter.set_ref_count(builder, type_instance, builder.const_int64(2))

        self.__gen_get_attr()
        self.__gen_set_attr()
        self.__gen_traverse()
        self.__gen_dealloc()

    def set_type_global_instance(self, var):
        self.__type_global_instance = var

    def get_type_global_instance(self):
        return self.__type_global_instance

    def __gen_traverse(self):
        pass

    def __gen_get_attr(self):
        pass

    def __gen_set_attr(self):
        pass

    def __gen_dealloc(self):
        pass

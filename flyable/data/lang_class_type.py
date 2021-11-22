import flyable.code_gen.ref_counter as ref_counter
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen
import flyable.code_gen.code_builder as code_builder
import flyable.code_gen.runtime as runtime
import flyable.code_gen.caller as caller


class LangClassType:
    """
    Class containing all of the relevant functions that need to be generated for a Python type definition
    """

    def __init__(self, _class):
        self.__lang_class = _class
        self.__type_global_instance = None
        self.__traverse_func = None
        self.__get_attr_func = None
        self.__set_attr_func = None
        self.__dealloc_func = None

    def setup(self, code_gen):
        global_instance = gen.GlobalVar("flyable@type@" + self.__lang_class.get_name(),
                                        code_type.get_py_type(code_gen).get_ptr_to(), gen.Linkage.INTERNAL)
        code_gen.add_global_var(global_instance)
        self.set_type_global_instance(global_instance)

    def generate(self, _class, code_gen, builder):
        """
        Generate the code that creates the type instance
        """
        type_instance_ptr = builder.global_var(self.get_type_global_instance())

        # Create the type instance
        class_alloc_func = code_gen.get_or_create_func("flyable_class_alloc",
                                                       code_type.get_py_type(code_gen).get_ptr_to(),
                                                       [], gen.Linkage.EXTERNAL)
        type_instance = builder.call(class_alloc_func, [])
        builder.store(type_instance, type_instance_ptr)

    def set_type_global_instance(self, var):
        self.__type_global_instance = var

    def get_type_global_instance(self):
        return self.__type_global_instance

import flyable.code_gen.ref_counter as ref_counter
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen


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

    def generate(self, _class, code_gen, builder):
        """
        Generate the code that creates the type instance
        """
        type_instance = builder.global_var(self.get_type_global_instance())

        # Set all attr to null
        py_obj_type_type = code_type.get_py_type(code_gen)
        type_struct = code_gen.get_struct(py_obj_type_type.get_struct_id())

        for index, struct in enumerate(type_struct.types_iter()):
            null_value = builder.const_null(struct)
            struct_ptr = builder.gep(type_instance, builder.const_int32(0), builder.const_int32(index))
            struct_ptr = builder.ptr_cast(struct_ptr, struct.get_ptr_to())
            builder.store(null_value, struct_ptr)

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

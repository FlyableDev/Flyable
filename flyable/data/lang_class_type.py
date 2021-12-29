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

        # Set all the attributes into the class map
        set_attr_func = code_gen.get_or_create_func("flyable_class_set_attr_index", code_type.get_void(),
                                                    [code_type.get_py_type(code_gen).get_ptr_to(),
                                                     code_type.get_int8_ptr(),
                                                     code_type.get_int32(),
                                                     code_type.get_int32()], gen.Linkage.EXTERNAL)

        for i, attribute in enumerate(_class.attributes_iter()):
            int_type = 3
            if attribute.get_type().is_int():
                int_type = 1
            elif attribute.get_type().is_dec():
                int_type = 2
            # The index suppose that every fields are 8 bytes long
            attr_str = builder.global_str(attribute.get_name() + "\00")
            attr_str = builder.ptr_cast(attr_str, code_type.get_int8_ptr())
            attr_index = (i * 8) + 16
            builder.call(set_attr_func,
                         [type_instance, attr_str, builder.const_int32(int_type), builder.const_int32(attr_index)])

        # Set all the methods tp/vec into the class map
        set_method_func = code_gen.get_or_create_func("flyable_class_set_method", code_type.get_void(),
                                                      [code_type.get_py_type(code_gen).get_ptr_to(),
                                                       code_type.get_int8_ptr(), code_type.get_int8_ptr(),
                                                       code_type.get_int8_ptr()],
                                                      gen.Linkage.EXTERNAL)

        for i, current_func in enumerate(_class.funcs_iter()):
            vec_impl = current_func.get_vec_call_impl()
            tp_impl = current_func.get_tp_call_impl()
            method_str = builder.global_str(current_func.get_name() + "\00")
            method_str = builder.ptr_cast(method_str, code_type.get_int8_ptr())
            tp_ptr = builder.ptr_cast(builder.func_ptr(tp_impl.get_code_func()), code_type.get_int8_ptr())
            vec_ptr = builder.ptr_cast(builder.func_ptr(vec_impl.get_code_func()), code_type.get_int8_ptr())
            builder.call(set_method_func, [type_instance, method_str, tp_ptr, vec_ptr])

    def set_type_global_instance(self, var):
        self.__type_global_instance = var

    def get_type_global_instance(self):
        return self.__type_global_instance

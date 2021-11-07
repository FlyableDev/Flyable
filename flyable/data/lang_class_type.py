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

        # Null all the fields
        for index, struct in enumerate(type_struct.types_iter()):
            null_value = builder.const_null(struct)
            struct_ptr = builder.gep(type_instance, builder.const_int32(0), builder.const_int32(index))
            struct_ptr = builder.ptr_cast(struct_ptr, struct.get_ptr_to())
            builder.store(null_value, struct_ptr)

        # Set the ref count to 2 to make sure that the type instance is not garbage collected
        ref_counter.set_ref_count(builder, type_instance, builder.const_int64(2))

       # self.__gen_get_attr()
       # self.__gen_set_attr()
       # self.__gen_traverse()
       # self.__gen_dealloc()

    def set_type_global_instance(self, var):
        self.__type_global_instance = var

    def get_type_global_instance(self):
        return self.__type_global_instance

    def __gen_traverse(self):
        pass

    def __gen_get_attr(self, _class):
        get_attr_func_name = "@flyable@class@get_attr@" + _class.get_name()

        get_attr_args = []

        get_attr_func = self.get_or_create_func(get_attr_func_name, code_type.get_int32(), get_attr_args,
                                                gen.Linkage.EXTERNAL)
        builder = code_builder.CodeBuilder(get_attr_func)
        entry_block = builder.create_block()

        builder.set_insert_block(entry_block)

    def __gen_get_attro(self, code_gen, _class):
        get_attro_func_name = "@flyable@class@get_attro@" + _class.get_name()
        get_attro_args = [code_type.get_py_obj_ptr(code_gen)] * 2
        get_attro_func = self.get_or_create_func(get_attro_func_name, code_type.get_py_type(code_gen), get_attro_args,
                                                 gen.Linkage.EXTERNAL)
        builder = code_builder.CodeBuilder(get_attro_func)
        entry_block = builder.create_block()

        builder.set_insert_block(entry_block)

        attr_blocks = []  # Block array that hold the jump to all
        attr_blocks_returns = []  # Block array that holds the instructions that returns the value
        for attr_index, attr in _class.attributes_iter():
            attr_blocks.append(builder.create_block())

        # Loop on all attributes and check if the attribute name is the same as the one we are looking for
        for attr_index, attr in _class.attributes_iter():
            current_block = attr_blocks[attr_index]
            builder.set_insert_block(current_block)

            attr_name = attr.get_name()
            attr_str = runtime.py_runtime_get_string(code_gen, builder, attr_name)
            is_true = builder.const_int1(1)

            if attr_index >= len(attr_blocks) - 1:  # If there is not attribute to get next
                builder.cond_br(is_true, current_return_block, not_found_block)
            else:
                builder.cond_br(is_true, current_return_block, attr_blocks[attr_index + 1])

    def __gen_set_attr(self):
        pass

    def __gen_dealloc(self):
        pass

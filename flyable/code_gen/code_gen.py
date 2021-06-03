import flyable.code_gen.code_writer as _writer
from flyable.code_gen.code_gen_visitor import CodeGenVisitor
from flyable.code_gen.code_writer import CodeWriter
from flyable.code_gen.code_builder import CodeBuilder
from flyable.code_gen.code_type import CodeType
import flyable.code_gen.code_type as code_type
import flyable.code_gen.runtime as runtime
import flyable.code_gen.library_loader as loader
import flyable.data.lang_type as lang_type
from collections import OrderedDict
import enum


class Linkage(enum.IntEnum):
    INTERNAL = 1,
    EXTERNAL = 2


class StructType:
    '''
    Represent a low-level structure defined by multiple CodeType
    '''

    def __init__(self, name):
        self.__name = name
        self.__types = []
        self.__id = 0

    def add_type(self, type):
        self.__types.append(type)

    def get_types_count(self):
        return len(self.__types)

    def get_type(self, index):
        return self.__types[index]

    def set_id(self, id):
        self.__id = id

    def get_id(self):
        return self.__id

    def to_code_type(self):
        return CodeType(CodeType.CodePrimitive.STRUCT, self.get_id())

    def write_to_code(self, writer):
        writer.add_str(self.__name)
        writer.add_int32(len(self.__types))
        for e in self.__types:
            e.write_to_code(writer)


class GlobalVar:
    '''
    Represent a low-level const address variable
    '''

    def __init__(self, name, type, linkage = Linkage.INTERNAL):
        self.__id = -1
        self.__name = name
        self.__type = type
        self.__initializer = None
        self.__linking = linkage

    def set_id(self, id):
        self.__id = id

    def get_id(self):
        return self.__id

    def get_name(self):
        return self.__name

    def get_type(self):
        return self.__type

    def set_initializer(self, data):
        self.__initializer = data

    def write_to_code(self, writer):
        writer.add_str(self.__name)
        self.__type.write_to_code(writer)
        writer.add_int32(self.__linking)


class CodeFunc:

    class CodeBlock:

        """
        CodeBlock represents a specific branch of code. It holds the instructions that the code builder will
        use to generate IR
        """

        def __init__(self, id=0):
            self.__code_writer = CodeWriter()
            self.__id = id
            self.__has_return = False
            self.__br_blocks = []

        def get_id(self):
            return self.__id

        def get_writer(self):
            return self.__code_writer

        def set_has_return(self, ret):
            self.__has_return = ret

        def has_return(self):
            return self.__has_return

        def write_to_code(self, writer):
            self.__code_writer.write_to_code(writer)

        def add_br_block(self, block):
            self.__br_blocks.append(block)

        def has_br_block(self):
            return len(self.__br_blocks) > 0

        def needs_end(self):
            """
            Return if the block points to no other block and has no ending (return instruction)
            """
            return self.has_br_block() == False and self.has_return() == False

        def __len__(self):
            return len(self.__code_writer.get_data())

    '''
    Represent a low level function with instructions
    '''

    def __init__(self, name):
        self.__id = -1
        self.__value_id = 0
        self.__linkage = Linkage.INTERNAL
        self.__name = name
        self.__args = []
        self.__return_type = CodeType()
        self.__blocks = []
        self.__builder = CodeBuilder(self)

    def set_linkage(self, link):
        self.__linkage = link

    def get_linkage(self):
        return self.__linkage

    def set_id(self, id):
        self.__id = id

    def get_id(self):
        return self.__id

    def set_return_type(self, type):
        self.__return_type = type

    def get_return_type(self):
        return self.__return_type

    def increment_value(self):
        result = self.__value_id
        self.__value_id += 1
        return result

    def add_arg(self, arg):
        self.__args.append(arg)
        self.__value_id += 1  # An argument represents a value

    def get_arg(self, index):
        return self.__args[index]

    def get_args_count(self):
        return len(self.__args)

    def add_block(self):
        self.__blocks.append(CodeFunc.CodeBlock(len(self.__blocks)))
        return self.__blocks[-1]

    def get_builder(self):
        return self.__builder

    def get_blocks_count(self):
        return len(self.__blocks)

    def get_block(self, index):
        return self.__blocks[index]

    def blocks_iter(self):
        return iter(self.__blocks)

    def get_name(self):
        return self.__name

    def write_to_code(self, writer):
        writer.add_str(self.__name)
        writer.add_int32(int(self.__linkage))
        self.__return_type.write_to_code(writer)
        writer.add_int32(len(self.__args))
        for arg in self.__args:
            arg.write_to_code(writer)

        writer.add_int32(len(self.__blocks))
        for block in self.__blocks:
            block.write_to_code(writer)


class CodeGen:

    def __init__(self):
        self.__global_vars = []
        self.__structs = []
        self.__funcs = OrderedDict()
        self.__data = None
        self.__strings = {}

        self.__true_var = self.add_global_var(GlobalVar("Py_True",code_type.get_int8_ptr(),Linkage.EXTERNAL))
        self.__false_var = self.add_global_var(GlobalVar("Py_False",code_type.get_int8_ptr(),Linkage.EXTERNAL))

    def generate(self, comp_data):
        self.__data = comp_data
        self.__gen_structs(comp_data)
        self.__fill_structs(comp_data)
        self.__gen_funcs(comp_data)
        self.__gen_vars(comp_data)

        self.__code_gen_func(comp_data)

        self.__generate_runtime()

        self.__generate_main()

        self.__write(comp_data)

    def get_data(self):
        return self.__data

    def get_c_string(self, str):
        if str in self.__strings:
            return self.__strings[str]
        new_str = GlobalVar("@flyable@str@" + str, CodeType(CodeType.CodePrimitive.INT8).get_ptr_to())
        self.__global_vars.append(new_str)
        self.__strings[str] = new_str

    def get_true(self):
        """
        Return the global variable containing the True python object
        """
        return self.__true_var

    def get_false(self):
        """
        Return the global variable containing the False python object
        """
        return self.__false_var

    def get_or_create_func(self, name, return_type, args_type, link= Linkage.INTERNAL):
        # Get case
        if name in self.__funcs:
            return self.__funcs[name]

        # Create case
        new_func = CodeFunc(name)
        new_func.set_linkage(link)
        for e in args_type:
            new_func.add_arg(e)
        new_func.set_return_type(return_type)
        new_func.set_id(len(self.__funcs))
        self.__funcs[name] = new_func

        return new_func

    def add_global_var(self, var):
        var.set_id(len(self.__global_vars))
        self.__global_vars.append(var)
        return var

    def __code_gen_func(self, comp_data):
        for func in comp_data.funcs_iter():
            for impl in func.impls_iter():
                if impl.is_unknown() == False:  # Only generate a function for known function
                    visitor = CodeGenVisitor(self, impl)
                    visitor.visit(func.get_node())
                    self.__fill_not_terminated_block(impl.get_code_func())

        for _class in comp_data.classes_iter():
            for func in _class.funcs_iter():
                for impl in func.impls_iter():
                    if impl.is_unknown() == False:  # Only visit functions with a complete signature
                        visitor = CodeGenVisitor(self, impl)
                        visitor.visit(func.get_node())
                        self.__fill_not_terminated_block(impl.get_code_func())

    def __gen_structs(self, comp_data):
        # Create all the structures
        for current_class in comp_data.classes_iter():
            new_struct = StructType("@flyable@__" + current_class.get_name())
            current_class.set_struct(new_struct)
            new_struct.set_id(len(self.__structs))
            self.__structs.append(new_struct)

    def __fill_structs(self, comp_data):
        # Fill all the structures
        for current_class in comp_data.classes_iter():
            for j in current_class.attributs_iter():
                attr = current_class.get_attribut(j)
                current_class.get_struct().add_type(attr.get_type().to_code_type())

    def __gen_funcs(self, comp_data):
        """
        Takes all implementations in functions and create all callables functions from it
        """
        for func in comp_data.funcs_iter():
            for i, impl in enumerate(func.impls_iter()):
                if impl.is_unknown() == False:
                    func_name = "@flyable@__" + func.get_name() + "@" + str(i) + "@" + str(func.get_id())
                    return_type = impl.get_return_type().to_code_type(comp_data)
                    func_args = lang_type.to_code_type(self.__data, list(impl.args_iter()))
                    new_func = self.get_or_create_func(func_name, return_type, func_args)
                    impl.set_code_func(new_func)

        for _class in comp_data.classes_iter():
            for func in _class.funcs_iter():
                for i, impl in enumerate(func.impls_iter()):
                    if impl.is_unknown() == False:
                        func_name = "@flyable@class@" + _class.get_name() + "@" + str(i) + "@" + str(func.get_id())
                        return_type = impl.get_return_type().to_code_type(comp_data)
                        func_args = lang_type.to_code_type(self.__data, list(impl.args_iter()))
                        new_func = self.get_or_create_func(func_name, return_type, func_args)
                        impl.set_code_func(new_func)

    def __fill_not_terminated_block(self, func):
        """
        Some blocks of code can end without any return. We need to generate
        the code so they can return nullified value
        """
        for block in func.blocks_iter():
            if block.has_br_block() is False and block.has_return() is False:
                func.get_builder().set_insert_block(block)
                func_return_type = func.get_return_type()
                if func_return_type == CodeType():
                    func.get_builder().ret_void()
                else:
                    func.get_buuilder().ret(func.get_builder.const_null(func_return_type))

    def __gen_vars(self, comp_data):
        pass

    def __write(self, comp_data):
        # Write all the data into a buffer to pass to the code generation native layer
        writer = _writer.CodeWriter()
        writer.add_str("**Flyable format**")

        # Add structs
        writer.add_int32(len(self.__structs))
        for _struct in self.__structs:
            writer.add_str("FlyableStruct")  # Name of the attr
            writer.add_int32(_struct.get_types_count())
            for attr in range(_struct.get_types_count()):
                attr.get_type(attr).write_to_code(writer)

        # Add global var
        writer.add_int32(len(self.__global_vars))
        for e in self.__global_vars:
            e.write_to_code(writer)

        # Add funcs
        writer.add_int32(len(self.__funcs))
        for e in self.__funcs.values():
            e.write_to_code(writer)

        loader.call_code_generation_layer(writer, comp_data.get_config("output"))

    def __generate_runtime(self):
        pass

    def __generate_main(self):
        """
        Generate Flyable program entry point.
        For now it's the found main function. In the future it should be the global module function #0
        """

        main_impl = self.__data.find_main().get_impl(1)

        # On Windows, an executable starts on the WinMain symbol
        main_func = self.get_or_create_func("WinMain", code_type.get_int32(), [], Linkage.EXTERNAL)
        builder = CodeBuilder(main_func)
        entry_block = builder.create_block()
        builder.set_insert_block(entry_block)

        runtime.py_runtime_init(self, builder)  # This call is required to properly starts the CPython interpreter

        # Create all the static Python string that we need
        for str in self.__strings:
            # TODO : Generate the string
            pass

        # Initialize all global vars
        # Set True global var
        # Set False global var

        return_value = builder.call(main_impl.get_code_func(), [])
        if main_impl.get_return_type().is_int():
            builder.ret(builder.int_cast(return_value, code_type.get_int32()))
        else:
            builder.ret(builder.const_int32(0))

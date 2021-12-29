import copy
import platform

import flyable.code_gen.code_writer as _writer
from flyable.code_gen.code_writer import CodeWriter
from flyable.code_gen.code_builder import CodeBuilder
from flyable.code_gen.code_type import CodeType
import flyable.code_gen.code_type as code_type
import flyable.code_gen.runtime as runtime
import flyable.code_gen.library_loader as loader
import flyable.data.lang_type as lang_type
import flyable.code_gen.module as gen_module
from collections import OrderedDict
import enum
import flyable.code_gen.ref_counter as ref_counter
import flyable.data.lang_func_impl as lang_func_impl


class Linkage(enum.IntEnum):
    INTERNAL = 1,
    EXTERNAL = 2


class CallingConv(enum.IntEnum):
    C = 1,
    FAST = 2


class StructType:
    """
    Represent a low-level structure defined by multiple CodeType
    """

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

    def types_iter(self):
        return iter(self.__types)

    def set_id(self, id):
        self.__id = id

    def get_id(self):
        return self.__id

    def get_name(self):
        return self.__name

    def to_code_type(self):
        return CodeType(CodeType.CodePrimitive.STRUCT, self.get_id())

    def write_to_code(self, writer):
        writer.add_str(self.__name)
        writer.add_int32(len(self.__types))
        for e in self.__types:
            e.write_to_code(writer)


class GlobalVar:
    """
    Represent a low-level const address variable
    """

    def __init__(self, name, type, linkage=Linkage.INTERNAL):
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
        writer.add_int32(int(self.__linking))


class CodeFunc:
    """
    Represents a low level function with machine instructions
    """

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
            writer.add_str(self.get_name())
            self.__code_writer.write_to_code(writer)

        def add_br_block(self, block):
            self.__br_blocks.append(block)

        def has_br_block(self):
            return len(self.__br_blocks) > 0

        def needs_end(self):
            """
            Return if the block points to no other block and has no ending (return instruction)
            """
            return not self.has_br_block() and not self.has_return()

        def __len__(self):
            return len(self.__code_writer.get_data())

        def get_name(self):
            return "Block@" + str(self.__id)

        def clear(self):
            self.__br_blocks.clear()
            self.__has_return = False

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

    def set_id(self, _id):
        self.__id = _id

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

    def get_args(self):
        return copy.copy(self.__args)

    def add_block(self):
        self.__blocks.append(CodeFunc.CodeBlock(len(self.__blocks)))
        return self.__blocks[-1]

    def get_builder(self):
        return self.__builder

    def clear_blocks(self):
        self.__blocks.clear()

    def get_blocks_count(self):
        return len(self.__blocks)

    def get_block(self, index):
        return self.__blocks[index]

    def blocks_iter(self):
        return iter(self.__blocks)

    def get_name(self):
        return self.__name

    def clear(self):
        self.__value_id = 0
        self.__return_type = CodeType()
        self.__blocks = []
        self.__builder = CodeBuilder(self)

    def write_to_code(self, writer):
        writer.add_str(self.__name)
        writer.add_int32(int(self.__linkage))
        self.__return_type.write_to_code(writer)
        writer.add_int32(len(self.__args))
        for arg in self.__args:
            arg.write_to_code(writer)

        writer.add_int32(self.__value_id + 1)

        writer.add_int32(len(self.__blocks))
        for block in self.__blocks:
            block.write_to_code(writer)


class CodeGen:

    def __init__(self, comp_data):
        self.__global_vars = []
        self.__structs = []
        self.__funcs = OrderedDict()
        self.__data = comp_data
        self.__global_strings = {}
        self.__py_constants = {}  # Global variable containing python constants

        self.__true_var = None
        self.__false_var = None
        self.__none_var = None
        self.__method_type = None
        self.__tuple_type = None
        self.__methode_type = None
        self.__build_in_module = None
        self.__python_obj_struct = None
        self.__python_list_struct = None
        self.__python_tuple_struct = None
        self.__python_func_struct = None
        self.__python_type_struct = None

    def setup(self):
        # Create the Python object struct
        self.__python_obj_struct = StructType("__flyable_py_obj")
        self.add_struct(self.__python_obj_struct)

        self.__python_type_struct = StructType("__flyable_py_type")
        self.add_struct(self.__python_type_struct)

        self.__python_obj_struct.add_type(code_type.get_int64())  # Py_ssize_t ob_refcnt
        self.__python_obj_struct.add_type(code_type.get_py_type(self).get_ptr_to())  # PyTypeObject * ob_type

        # Create the Python list struct
        self.__python_list_struct = StructType("__flyable_py_obj_list")
        self.__python_list_struct.add_type(code_type.get_int64())  # ob_refcnt
        self.__python_list_struct.add_type(code_type.get_int8_ptr())  # ob_type
        self.__python_list_struct.add_type(code_type.get_int64())  # ob_size
        self.__python_list_struct.add_type(code_type.get_int8_ptr().get_ptr_to())  # ob_item
        self.__python_list_struct.add_type(code_type.get_int64())  # allocated
        self.add_struct(self.__python_list_struct)

        # Create the Python tuple struct
        self.__python_tuple_struct = StructType("__flyable_py_obj_tuple")
        self.__python_tuple_struct.add_type(code_type.get_int64())  # ob_refcnt
        self.__python_tuple_struct.add_type(code_type.get_int8_ptr())  # ob_type
        self.__python_tuple_struct.add_type(code_type.get_int64())  # ob_size
        self.__python_tuple_struct.add_type(code_type.get_py_obj_ptr(self))  # ob_item
        self.add_struct(self.__python_tuple_struct)

        # Create the Python function struct
        self.__python_func_struct = StructType("__flyable_py_obj_func")
        self.__python_func_struct.add_type(code_type.get_int64())  # Py_ssize_t ob_refcnt
        self.__python_func_struct.add_type(code_type.get_py_obj_ptr(self))  # PyTypeObject * ob_type
        self.__python_func_struct.add_type(code_type.get_int8_ptr())  # tp_name
        self.__python_func_struct.add_type(code_type.get_int64())  # tp_basicsize
        self.__python_func_struct.add_type(code_type.get_int64())  # tp_itemsize
        self.__python_func_struct.add_type(code_type.get_int8_ptr())  # tp_dealloc

        for i in range(12):
            self.__python_func_struct.add_type(code_type.get_py_obj_ptr(self))
        self.__python_func_struct.add_type(code_type.get_int8_ptr())  # vectorcall
        self.add_struct(self.__python_func_struct)

        # Create the python type object struct
        self.__python_type_struct.add_type(code_type.get_int64())  # Py_ssize_t ob_refcnt
        self.__python_type_struct.add_type(self.get_python_type().to_code_type().get_ptr_to())  # PyTypeObject * ob_type
        self.__python_type_struct.add_type(code_type.get_int64())  # size_t ob_size
        self.__python_type_struct.add_type(code_type.get_int8_ptr())  # tp_name
        self.__python_type_struct.add_type(code_type.get_int64())  # tp_basicsize
        self.__python_type_struct.add_type(code_type.get_int64())  # tp_itemsize
        self.__python_type_struct.add_type(code_type.get_int8_ptr())  # tp_dealloc
        self.__python_type_struct.add_type(code_type.get_int64())  # tp_vectorcall_offset
        self.__python_type_struct.add_type(code_type.get_int8_ptr())  # getattr
        self.__python_type_struct.add_type(code_type.get_int8_ptr())  # setattr
        self.__python_type_struct.add_type(code_type.get_int8_ptr())  # tp_as_async
        self.__python_type_struct.add_type(code_type.get_int8_ptr())  # tp_repr
        self.__python_type_struct.add_type(code_type.get_py_obj_ptr(self))  # tp_as_number
        self.__python_type_struct.add_type(code_type.get_py_obj_ptr(self))  # tp_as_sequence
        self.__python_type_struct.add_type(code_type.get_py_obj_ptr(self))  # tp_as_mapping
        self.__python_type_struct.add_type(code_type.get_int8_ptr())  # tp_hash
        self.__python_type_struct.add_type(code_type.get_int8_ptr())  # tp_call
        self.__python_type_struct.add_type(code_type.get_int8_ptr())  # tp_str
        self.__python_type_struct.add_type(code_type.get_int8_ptr())  # tp_getattro
        self.__python_type_struct.add_type(code_type.get_int8_ptr())  # tp_setattro
        self.__python_type_struct.add_type(code_type.get_py_obj_ptr(self))  # tp_as_buffer
        self.__python_type_struct.add_type(code_type.get_int32())  # tp_flags
        self.__python_type_struct.add_type(code_type.get_int8_ptr())  # tp_doc
        for i in range(25): self.__python_type_struct.add_type(code_type.get_int8_ptr())
        self.__python_type_struct.add_type(code_type.get_int32())  # tp_version_tag
        self.__python_type_struct.add_type(code_type.get_int8_ptr())  # tp_finalize
        self.__python_type_struct.add_type(code_type.get_int8_ptr())  # tp_vectorcall

        self.__true_var = self.add_global_var(
            GlobalVar("@Flyable@_True", code_type.get_py_obj_ptr(self), Linkage.INTERNAL))
        self.__false_var = self.add_global_var(
            GlobalVar("@Flyable@_False", code_type.get_py_obj_ptr(self), Linkage.INTERNAL))
        self.__none_var = self.add_global_var(
            GlobalVar("@Flyable@_None", code_type.get_py_obj_ptr(self), Linkage.INTERNAL))
        self.__py_func_type_var = self.add_global_var(
            GlobalVar("PyFunction_Type", code_type.get_py_obj(self), Linkage.EXTERNAL))
        self.__method_type = self.add_global_var(
            GlobalVar("PyMethod_Type", code_type.get_py_obj(self), Linkage.EXTERNAL))
        self.__tuple_type = self.add_global_var(
            GlobalVar("PyTuple_Type", code_type.get_py_obj_ptr(self), Linkage.EXTERNAL))
        self.__method_type = self.add_global_var(
            GlobalVar("PyMethod_Type", code_type.get_py_obj(self), Linkage.EXTERNAL))

        self.__build_in_module = self.add_global_var(GlobalVar("__flyable@BuildIn@Module@",
                                                               code_type.get_py_obj_ptr(self), Linkage.INTERNAL))

        for _class in self.__data.classes_iter():
            self.gen_struct(_class)

    def clear(self):
        self.__global_vars.clear()
        self.__funcs.clear()
        self.__structs.clear()
        self.__global_strings.clear()
        self.__py_constants.clear()

    def get_data(self):
        return self.__data

    def get_c_string(self, str):
        if str in self.__strings:
            return self.__strings[str]
        new_str = GlobalVar("@flyable@str@" + str, CodeType(CodeType.CodePrimitive.INT8).get_ptr_to(), Linkage.INTERNAL)
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

    def get_none(self):
        """
        Return the global variable containing the None python object
        """
        return self.__none_var

    def get_py_func_type(self):
        """
        Return the global variable containing the PyFunctionObject python type
        """
        return self.__py_func_type_var

    def get_method_type(self):
        return self.__method_type

    def get_tuple_type(self):
        return self.__tuple_type

    def get_method_type(self):
        """
        return the global variable containing the Python method type
        """
        return self.__method_type

    def get_build_in_module(self):
        """
        return the build-in module
        """
        return self.__build_in_module

    def get_py_obj_struct(self):
        return self.__python_obj_struct

    def get_py_list_struct(self):
        return self.__python_list_struct

    def get_py_tuple_struct(self):
        return self.__python_tuple_struct

    def get_py_func_struct(self):
        return self.__python_func_struct

    def get_python_type(self):
        """
        return the variable containing the Python type struct
        """
        return self.__python_type_struct

    def get_or_create_func(self, name, return_type, args_type=[], link=Linkage.INTERNAL):
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

    def get_or_insert_str(self, value):
        if value in self.__global_strings:
            return self.__global_strings[value]

        new_var = GlobalVar("@flyable@str" + str(len(self.__global_strings)), code_type.get_py_obj_ptr(self),
                            Linkage.INTERNAL)
        self.add_global_var(new_var)
        self.__global_strings[value] = new_var
        return new_var

    def get_or_insert_const(self, value):
        try:
            return self.__py_constants[value]
        except KeyError:
            pass

        if not isinstance(value, int) and not isinstance(value, float):
            raise ValueError("Const type " + str(type(value)) + " not expected")

        var_type = code_type.get_int64()
        name = "@flyable@const@" + str(len(self.__py_constants))
        new_var = GlobalVar(name, code_type.get_py_obj_ptr(self), Linkage.INTERNAL)
        self.add_global_var(new_var)
        self.__py_constants[value] = new_var
        return new_var

    def add_struct(self, struct):
        struct.set_id(len(self.__structs))
        self.__structs.append(struct)

    def get_struct(self, index):
        return self.__structs[index]

    def add_global_var(self, var):
        var.set_id(len(self.__global_vars))
        self.__global_vars.append(var)
        return var

    def gen_struct(self, _class):
        """
        Create a structure from a class and creates the global variable that will hold the type instance of that class
        """
        # Create the struct
        new_struct = StructType("@flyable@__" + _class.get_name())
        _class.set_struct(new_struct)
        self.add_struct(new_struct)

        # Create the global variable to hold it
        # The allocation is static and not dynamic
        _class.get_class_type().setup(self)

    def setup_struct(self):
        for _class in self.__data.classes_iter():
            _class.get_struct().add_type(code_type.get_int64())  # Py_ssize_t ob_refcnt
            _class.get_struct().add_type(code_type.get_py_type(self).get_ptr_to())  # PyTypeObject * ob_type
            for attribute in _class.attributes_iter():
                _class.get_struct().add_type(attribute.get_type().to_code_type(self))

    def gen_func(self, impl):
        """
        Take an implementation  and create a callable CodeFunction from it
        """
        class_name = ""
        if impl.get_parent_func().get_class() is not None:
            class_name = impl.get_parent_func().get_class().get_name()
        func_name = "@flyable@__" + class_name + "@" + impl.get_parent_func().get_name() + "@" + \
                    str(impl.get_id()) + "@" + str(impl.get_parent_func().get_id()) + "@" + str(impl.get_id())
        return_type = impl.get_return_type().to_code_type(self)

        if impl.get_impl_type() == lang_func_impl.FuncImplType.SPECIALIZATION:
            func_args = lang_type.to_code_type(self, list(impl.args_iter()))
        elif impl.get_impl_type() == lang_func_impl.FuncImplType.TP_CALL:
            func_args = [code_type.get_py_obj_ptr(self)] * 3
            return_type = code_type.get_py_obj_ptr(self)
        elif impl.get_impl_type() == lang_func_impl.FuncImplType.VEC_CALL:
            func_args = [code_type.get_py_obj_ptr(self), code_type.get_py_obj_ptr(self).get_ptr_to(),
                         code_type.get_int64(), code_type.get_py_obj_ptr(self)]
            return_type = code_type.get_py_obj_ptr(self)
        else:
            raise ValueError("Only spec, tp, of vec function can be code generate")

        new_func = self.get_or_create_func(func_name, return_type, func_args)
        impl.set_code_func(new_func)
        return new_func

    def fill_not_terminated_block(self, visitor):
        """
        Some blocks of code can end without any return. We need to generate
        the code so they can return nullified value
        """
        builder = visitor.get_builder()
        func = visitor.get_func().get_code_func()
        for block in func.blocks_iter():
            if not block.has_br_block() and not block.has_return():
                func.get_builder().set_insert_block(block)
                func_return_type = func.get_return_type()
                ref_counter.decr_all_variables(visitor)
                if func_return_type == CodeType():
                    func.get_builder().ret_void()
                elif visitor.get_func().get_return_type() == lang_type.get_python_obj_type():
                    none_value = builder.load(builder.global_var(self.get_none()))
                    ref_counter.ref_incr(builder, lang_type.get_python_obj_type(), none_value)
                    builder.ret(none_value)
                else:
                    func.get_builder().ret(func.get_builder().const_null(func_return_type))

    def write(self):
        # Write all the data into a buffer to pass to the code generation native layer
        writer = _writer.CodeWriter()
        writer.add_str("**Flyable format**")

        # Add structs
        writer.add_int32(len(self.__structs))
        for _struct in self.__structs:
            writer.add_str("FlyableStruct@" + _struct.get_name())  # Name of the attr
            writer.add_int32(_struct.get_types_count())
            for attr in range(_struct.get_types_count()):
                _struct.get_type(attr).write_to_code(writer)

        # Add global var
        writer.add_int32(len(self.__global_vars))
        for e in self.__global_vars:
            e.write_to_code(writer)

        # Add funcs
        writer.add_int32(len(self.__funcs))
        for e in self.__funcs.values():
            e.write_to_code(writer)

        loader.call_code_generation_layer(writer, self.__data.get_config("output"))

    def generate_main(self, main_impl):
        """
        Generate Flyable program entry point.
        """

        # On Windows, an executable starts on the WinMain symbol
        if platform.uname()[0] == "Windows":
            main_name = "WinMain"
        elif platform.uname()[0] == "Linux":
            main_name = "main"
        else:
            raise NotImplemented(platform.uname()[0] + " not supported")

        main_func = self.get_or_create_func(main_name, code_type.get_int32(), [], Linkage.EXTERNAL)
        builder = CodeBuilder(main_func)
        entry_block = builder.create_block()
        builder.set_insert_block(entry_block)

        runtime.py_runtime_init(self, builder)  # This call is required to properly starts the CPython interpreter

        # Create all the static Python string that we need
        for global_str in self.__global_strings.items():
            new_str = runtime.py_runtime_get_string(self, builder, global_str[0])
            builder.store(new_str, builder.global_var(global_str[1]))

        # Initialize all global vars
        # Set True global var
        true_type, true_value = runtime.value_to_pyobj(self, builder, builder.const_int1(1), lang_type.get_bool_type())
        builder.store(true_value, builder.global_var(self.get_true()))

        # Set False global var
        false_type, false_value = runtime.value_to_pyobj(self, builder, builder.const_int1(0),
                                                         lang_type.get_bool_type())
        builder.store(false_value, builder.global_var(self.get_false()))

        # Set None global var
        none_value = builder.call(
            self.get_or_create_func("flyable_get_none", code_type.get_py_obj_ptr(self), [], Linkage.EXTERNAL), [])
        builder.store(none_value, builder.global_var(self.get_none()))

        # Set the build-in module
        build_in_module = gen_module.import_py_module(self, builder, "builtins")
        builder.store(build_in_module, builder.global_var(self.get_build_in_module()))
        # Set the tuple type
        tuple_func_type = self.get_or_create_func("flyable_get_tuple_type", code_type.get_py_obj_ptr(self), [],
                                                  Linkage.EXTERNAL)
        builder.store(builder.call(tuple_func_type, []), builder.global_var(self.get_tuple_type()))

        # Set the constant
        for key in self.__py_constants.keys():
            constant_var = builder.global_var(self.__py_constants[key])
            if isinstance(key, int):
                value_to_convert = builder.const_int64(key)
                type_to_assign, value_to_assign = runtime.value_to_pyobj(self, builder, value_to_convert,
                                                                         lang_type.get_int_type())
            else:
                value_to_convert = builder.const_float64(key)
                type_to_assign, value_to_assign = runtime.value_to_pyobj(self, builder, value_to_convert,
                                                                         lang_type.get_dec_type())
            builder.store(value_to_assign, constant_var)

        # Create all the instances of type
        # Put their ref count to 2 to avoid decrement delete
        for _class in self.__data.classes_iter():
            _class.get_class_type().generate(_class, self, builder)

        return_value = builder.call(main_impl.get_code_func(), [])
        if main_impl.get_return_type().is_int():
            builder.ret(builder.int_cast(return_value, code_type.get_int32()))
        else:
            builder.ret(builder.const_int32(0))

    def convert_type(self, builder, type_from, value, type_to):
        if type_to.is_python_obj():
            return runtime.value_to_pyobj(self, builder, value, type_from)[1]
        elif type_to.is_obj():
            return builder.ptr_cast(type_to.get_id())
        raise ValueError("Impossible to convert the type")

    def get_null_from_type(self, builder, type):
        if type.is_int():
            return builder.const_int64(0)
        elif type.is_dec():
            return builder.const_float64(0.0)
        elif type.is_bool():
            return builder.const_int1(False)
        else:
            return builder.const_null(type.to_code_type(self.__data))

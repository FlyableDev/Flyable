from __future__ import annotations
from typing import TYPE_CHECKING
import flyable.code_gen.ref_counter as ref_counter
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as gen
import flyable.code_gen.code_builder as code_builder
import flyable.code_gen.runtime as runtime
import flyable.code_gen.caller as caller
import flyable.code_gen.code_gen as _gen

if TYPE_CHECKING:
    from flyable.code_gen.code_gen import CodeGen
    from flyable.data.lang_class import LangClass


class LangClassType:
    """
    Class containing all of the relevant functions that need to be generated for a Python type definition
    """

    def __init__(self, _class: LangClass):
        self.__lang_class = _class
        self.__traverse_func = None
        self.__get_attr_func = None
        self.__set_attr_func = None
        self.__dealloc_func = None

    def generate(self, _class: LangClass, code_gen: CodeGen, builder: code_builder.CodeBuilder):
        """
        Generate the code that creates the type instance
        """
        func_add_impl = code_gen.get_or_create_func("flyable_add_impl", code_type.get_void(),
                                                    [code_type.get_int8_ptr()] * 3,
                                                    _gen.Linkage.EXTERNAL)
        for i in range(_class.get_funcs_count()):
            func = _class.get_func(i)
            tp_func = func.get_tp_call_impl()
            vec_func = func.get_vec_call_impl()
            impl_name = builder.ptr_cast(builder.global_str(func.get_qualified_name() + "\0"),
                                         code_type.get_int8_ptr())
            tp_func = builder.ptr_cast(builder.func_ptr(tp_func.get_code_func()), code_type.get_int8_ptr())
            vec_func = builder.ptr_cast(builder.func_ptr(vec_func.get_code_func()), code_type.get_int8_ptr())
            builder.call(func_add_impl, [impl_name, tp_func, vec_func])

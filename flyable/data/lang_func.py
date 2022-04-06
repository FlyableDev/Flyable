from __future__ import annotations
from typing import TYPE_CHECKING, Iterator, Optional

import ast

import flyable.data.lang_file as lang_file
from flyable.data.lang_func_impl import LangFuncImpl, FuncImplType
import flyable.code_gen.code_type as code_type
import flyable.code_gen.code_gen as _gen


class LangFunc:
    """
    Represents a class definition
    Ex:
    def my_func(a,b):
        body....
    """

    def __init__(self, node: ast.FunctionDef | ast.Module):
        self.__node: ast.FunctionDef | ast.Module = node
        self.__impls = []
        self.__id: int = -1
        self.__setup_python_impl()
        self.__file = None

    def set_id(self, id: int):
        self.__id = id

    def get_id(self):
        return self.__id

    def add_impl(self, func: LangFuncImpl):
        func.set_parent_func(self)
        func.set_id(len(self.__impls))
        self.__impls.append(func)

    def remove_impl(self, func: LangFuncImpl):
        self.__impls.remove(func)

    def get_impl(self, index: int):
        return self.__impls[index]

    def get_impl_iter(self):
        return iter(self.__impls)

    def set_file(self, file: lang_file.LangFile):
        self.__file = file

    def get_file(self):
        return self.__file

    def get_source_code(self):
        return ast.get_source_segment(source=self.get_file().get_text(), node=self.__node)

    def get_impls_count(self):
        return len(self.__impls)

    def impls_iter(self):
        return iter(self.__impls)

    def get_unknown_impl(self):
        return self.__impls[0]

    def get_node(self):
        return self.__node

    def get_name(self):
        return "@global@module@" + self.__node.name

    def get_tp_call_impl(self):
        for impl in self.__impls:
            if impl.get_impl_type() is FuncImplType.TP_CALL:
                return impl
        return None

    def get_vec_call_impl(self):
        for impl in self.__impls:
            if impl.get_impl_type() is FuncImplType.VEC_CALL:
                return impl
        return None

    def __setup_python_impl(self):
        # setup the tp call
        python_impl = LangFuncImpl()
        self.__impls.append(python_impl)
        python_impl.set_parent_func(self)
        python_impl.set_impl_type(FuncImplType.TP_CALL)

        # setup the vec call
        python_impl = LangFuncImpl()
        self.__impls.append(python_impl)
        python_impl.set_parent_func(self)
        python_impl.set_impl_type(FuncImplType.VEC_CALL)

    def get_qualified_name(self):
        name = self.__node.name
        return name

    def generate_code_to_set_impl(self, code_gen, builder):
        """
        Generate the code that creates implementation inside CPython
        """
        func_add_impl = code_gen.get_or_create_func("flyable_add_impl", code_type.get_void(),
                                                    [code_type.get_int8_ptr()] * 3,
                                                    _gen.Linkage.EXTERNAL)
        tp_func = self.get_tp_call_impl()
        vec_func = self.get_vec_call_impl()
        if tp_func is not None and vec_func is not None:
            impl_name = builder.ptr_cast(builder.global_str(self.get_qualified_name() + "\0"), code_type.get_int8_ptr())
            tp_func = builder.ptr_cast(builder.func_ptr(tp_func.get_code_func()), code_type.get_int8_ptr())
            vec_func = builder.ptr_cast(builder.func_ptr(vec_func.get_code_func()), code_type.get_int8_ptr())
            builder.call(func_add_impl, [impl_name, tp_func, vec_func])

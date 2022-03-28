from __future__ import annotations
from typing import TYPE_CHECKING, Iterator, Optional

if TYPE_CHECKING:
    from flyable.data.lang_class import LangClass

import ast

import flyable.data.lang_type as type
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

        self.__id: int = -1
        # Setup args
        self.__setup_unknown_impl()
        self.__setup_python_impl()

        self.__class_lang: LangClass | None = None
        self.__file: lang_file.LangFile | None = None
        self.__is_global = False

    def set_class(self, _class: LangClass):
        self.__class_lang = _class

    def get_class(self):
        return self.__class_lang

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

    def get_impls_count(self):
        return len(self.__impls)

    def impls_iter(self):
        return iter(self.__impls)

    def find_impl_by_signature(
            self, args_type: list[type.LangType]
    ) -> LangFuncImpl | None:
        for impl in self.__impls:
            if not impl.is_unknown() and impl.get_args_count() == len(
                    args_type
            ):  # Same arguments count
                same_signature = True
                for arg, arg_type in zip(impl.get_args(), args_type):
                    if arg != arg_type:
                        same_signature = False
                        break

                if not impl.get_impl_type() == FuncImplType.SPECIALIZATION:
                    same_signature = False

                if same_signature:
                    return impl
        return None

    def get_min_args(self):
        """
        Returns the minimal amount of arguments required to call.
        """
        # Amount of total args vs the amount of args with default values
        if isinstance(self.__node, ast.FunctionDef):
            return len(self.__node.args.args) - len(self.__node.args.defaults)
        return 0

    def get_max_args(self):
        """
        Returns the maximum amount that can be used on this function.
        -1 means varargs
        """
        if isinstance(self.__node, ast.FunctionDef):
            return len(self.__node.args.args)
        return 0

    def get_unknown_impl(self):
        return self.__impls[0]

    def get_node(self):
        return self.__node

    def get_name(self):
        if isinstance(self.__node, ast.FunctionDef):
            return self.__node.name
        return "@global@module@"

    def get_arg(self, index: int):
        if isinstance(self.__node, ast.Module):
            raise TypeError("Cannot get argument of LangFunc, it is an ast.Module")
        return self.__node.args.args[index]

    def get_args_count(self):
        if isinstance(self.__node, ast.FunctionDef):
            arg_node = self.__node.args
            return len(arg_node.args)
        return 0

    def args_iter(self) -> Iterator[ast.arg]:
        if isinstance(self.__node, ast.FunctionDef):
            return iter(self.__node.args.args)
        return iter([])

    def args_format(self) -> list[tuple[str, Optional[str]]]:
        """
        Returns a list of tuples with the format of the argument
        Ex:

        >>> def abc(param1: int, param2: str, param3):
        >>> [('param1', 'int'), ('param2', 'str'), ('param3', None)]
        """
        return [
            (arg.arg, (arg.annotation and arg.annotation.id))
            for arg in self.args_iter()
        ]

    def set_global(self, _global: bool):
        self.__is_global = _global

    def is_global(self):
        return self.__is_global

    def clear_info(self):

        global_impl = None
        if self.is_global():
            global_impl = self.__impls[2]
            global_impl.clear_info()

        self.__impls.clear()
        self.__setup_unknown_impl()
        self.__setup_python_impl()

        if global_impl is not None:
            self.__impls.append(global_impl)

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

    def __setup_unknown_impl(self):
        # Setup args
        self.__impls = [LangFuncImpl()]
        self.__impls[0].set_parent_func(self)
        self.__impls[0].set_unknown(True)
        for e in self.args_iter():
            self.get_unknown_impl().add_arg(type.get_unknown_type())

    def __setup_python_impl(self):
        # setup the tp call
        python_impl = LangFuncImpl()
        self.__impls.append(python_impl)
        python_impl.set_parent_func(self)
        python_impl.set_unknown(False)
        python_impl.set_impl_type(FuncImplType.TP_CALL)
        python_impl.set_return_type(type.get_python_obj_type())
        for e in self.args_iter():
            python_impl.add_arg(type.get_python_obj_type())

        # setup the vec call
        python_impl = LangFuncImpl()
        self.__impls.append(python_impl)
        python_impl.set_parent_func(self)
        python_impl.set_unknown(False)
        python_impl.set_impl_type(FuncImplType.VEC_CALL)
        python_impl.set_return_type(type.get_python_obj_type())
        for e in self.args_iter():
            python_impl.add_arg(type.get_python_obj_type())

    def get_qualified_name(self):
        name = self.__node.name
        if self.__class_lang:
            return f"{self.__class_lang.get_qualified_name()}.{name}"
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
        impl_name = builder.ptr_cast(builder.global_str(self.get_qualified_name() + "\0"), code_type.get_int8_ptr())
        tp_func = builder.ptr_cast(builder.func_ptr(tp_func.get_code_func()), code_type.get_int8_ptr())
        vec_func = builder.ptr_cast(builder.func_ptr(vec_func.get_code_func()), code_type.get_int8_ptr())
        builder.call(func_add_impl, [impl_name, tp_func, vec_func])

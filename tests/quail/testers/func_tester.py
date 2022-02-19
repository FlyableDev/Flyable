from __future__ import annotations

from dataclasses import dataclass

from flyable.data import lang_type
from flyable.data.comp_data import CompData
from flyable.data.lang_func import LangFunc
import flyable.data.type_hint as hint


def _into_lang_type(arg_type: type):
    primitive_types = {
        "int": lang_type.get_int_type(),
        "float": lang_type.get_dec_type(),
        "bool": lang_type.get_bool_type(),
        "set": lang_type.get_set_of_python_obj_type(),
        "dict": lang_type.get_dict_of_python_obj_type(),
        "list": lang_type.get_list_of_python_obj_type(),
        "tuple": lang_type.get_tuple_of_python_obj_type(),
    }
    if arg_type.__name__ not in primitive_types:
        return lang_type.get_python_obj_type(hint.TypeHintPythonType(arg_type.__name__))
    return primitive_types[arg_type.__name__]


@dataclass
class FunctionTester:
    __data: CompData
    func: LangFunc

    @property
    def __msg_err(self):
        name = self.func.get_name()
        return f"The function {name!r}"

    def has_impl(self, *args_type: type, return_type: type = None):
        name = self.func.get_name()
        lang_args_type = [_into_lang_type(arg_type) for arg_type in args_type]
        if self.func.find_impl_by_signature(lang_args_type) is not None:
            return self
        assert (
            False
        ), f"{self.__msg_err} doesn't have an implentation that matches {name}{args_type!r}."

    def matches_args_format(self, *args_format: tuple[str, str] | tuple[str]):
        """
        :param args_format: a varargs of tuples of form (arg_name,) or (arg_name, arg_annotation)
        :return:
        """
        actual_args_format = self.func.args_format()

        def show_diff():
            name = self.func.get_name()
            return (
                f"Expected format of function {name!r}:\n"
                f"{name}({','.join(f'{expected[0]}: {expected[1]}' if len(expected) == 2 else expected[0] for expected in args_format)})\n"
                + ("-" * 30)
                + "\n"
                + f"Actual format of function {name!r}\n"
                + f"{name}({','.join(f'{arg_name}: {arg_annotation}' if arg_annotation else arg_name for (arg_name, arg_annotation) in actual_args_format)})"
            )

        error_msg = (
            f"The expected format doesn't match the actual format:\n\n{show_diff()}"
        )

        assert len(actual_args_format) == len(args_format), error_msg

        for (arg_name, arg_annotation), expected_format in zip(
            actual_args_format, args_format, strict=True
        ):
            assert arg_name == expected_format[0], error_msg
            if len(expected_format) == 2:
                assert arg_annotation == expected_format[1], error_msg

        return self

    def is_global(self):
        assert self.func.is_global(), f"{self.__msg_err} is not global"
        return self

    def is_not_global(self):
        assert not self.func.is_global(), f"{self.__msg_err} is global"
        return self

    def supports_tp_calls(self):
        """"""
        assert (
            self.func.get_tp_call_impl() is not None
        ), f"{self.__msg_err} doesn't support the tp call protocol"
        return self

    def supports_vec_calls(self):
        """"""
        assert (
            self.func.get_vec_call_impl() is not None
        ), f"{self.__msg_err} doesn't support the vector call protocol"
        return self

    def in_file(self, path: str):
        file = self.func.get_file()
        assert file is not None, f"{self.__msg_err} is not defined at path {path!r}"
        assert file.get_path() == path, (
            f"{self.__msg_err} is not defined at path {path!r}"
            f" but at path {file.get_path()!r}"
        )
        return self

    def in_class(self, class_name: str):
        cls = self.func.get_class()
        assert (
            cls is not None
        ), f"{self.__msg_err} is not defined in class {class_name!r}"
        assert cls.get_name() == class_name, (
            f"{self.__msg_err} is not defined in class {class_name!r}"
            f" but in {cls.get_name()!r}"
        )
        return self

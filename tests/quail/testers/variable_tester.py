from __future__ import annotations

from dataclasses import dataclass

from flyable.data.comp_data import CompData
from flyable.data.lang_func import LangFunc
from flyable.parse.variable import Variable
from tests.quail.testers.utils import into_lang_type, into_type
import flyable.data.type_hint as hint


@dataclass
class VariableTester:
    __data: CompData
    var: Variable

    @property
    def __msg_err(self):
        name = self.var.get_name()
        return f"The variable {name!r}"

    def is_of_type(self, expected_var_type: type | str):
        """

        :param expected_var_type: if isinstance(str) -> must contain the module in the argument
        (ex: 'builtins.str' instead of 'str')
        :return:
        """

        def get_name_of_type():
            if (t := hint.get_lang_type_contained_hint_type(var_type, hint.TypeHintPythonType)) is not None:
                name = t.get_class_path()

            elif (t := hint.get_lang_type_contained_hint_type(var_type, hint.TypeHintConstValue)) is not None:
                v = t.get_value().__class__
                name = f"{v.__module__}.{v.__name__}"
            elif (t := hint.get_type_source(var_type)) is not None:
                name = t.get_source().get_name()
            else:
                raise ValueError("The type could not be found because there was no type hints")
            return name

        _t = into_lang_type(expected_var_type)
        if isinstance(expected_var_type, type):
            expected_var_path = f"{expected_var_type.__module__}.{expected_var_type.__name__}"
        else:
            expected_var_path = expected_var_type
        var_type = self.var.get_type()

        assert hint.is_python_type(var_type, expected_var_path) or hint.is_const_type(var_type, expected_var_type), (
            f"{self.__msg_err} was expected to be of type {expected_var_path!r} "
            f"but was of type {get_name_of_type()!r}")

    def print(self):
        print(self.var.get_name())

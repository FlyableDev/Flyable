from flyable.data import lang_type
import flyable.data.type_hint as hint
from flyable.data.lang_type import LangType
from flyable.tool.utils import find_first

_primitive_types = {
    "int": lang_type.get_int_type(),
    "float": lang_type.get_dec_type(),
    "bool": lang_type.get_bool_type(),
    "set": lang_type.get_set_of_python_obj_type(),
    "dict": lang_type.get_dict_of_python_obj_type(),
    "list": lang_type.get_list_of_python_obj_type(),
    "tuple": lang_type.get_tuple_of_python_obj_type(),
    "str": lang_type.get_str_type()
}


def into_lang_type(arg_type: type):
    if arg_type.__name__ not in _primitive_types:
        return lang_type.get_python_obj_type(hint.TypeHintPythonType(arg_type.__name__))
    return _primitive_types[arg_type.__name__]


def into_type(arg_type: LangType):
    if arg_type not in _primitive_types.values():
        raise ValueError
    return find_first(lambda t: t[1] == arg_type, _primitive_types.items())

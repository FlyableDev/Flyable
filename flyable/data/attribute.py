import flyable.data.lang_type as type
import copy
import flyable.data.type_hint as hint


class Attribut:

    def __init__(self):
        self.__name = ""
        self.__type = type.LangType()
        self.__id = - 1

    def set_id(self, id):
        self.__id = id

    def get_id(self):
        return self.__id

    def set_name(self, name):
        self.__name = name

    def get_name(self):
        return self.__name

    def set_type(self, s_type: type.LangType):
        self.__type = copy.copy(s_type)
        hint.remove_hint_type(self.__type, hint.TypeHintDataSource)

    def get_type(self):
        return self.__type

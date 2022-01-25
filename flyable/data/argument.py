import flyable.data.lang_type as lang_type


class Argument:

    def __init__(self, name:str="", _type:lang_type.LangType=lang_type.get_unknown_type()):
        self.__name = name
        self.__type = _type

    def get_name(self):
        return self.__name

    def get_type(self):
        return self.__type

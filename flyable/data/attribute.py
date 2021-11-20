import flyable.data.lang_type as type


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

    def set_type(self, s_type):
        self.__type = s_type

    def get_type(self):
        return self.__type

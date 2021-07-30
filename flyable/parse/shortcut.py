import flyable.code_gen.list as gen_list
import flyable.data.lang_type as lang_type

"""
Shortcut is a module to generate code that aims to bypass call to the interpreter
"""


class ShortcutObjCall:

    def __init__(self):
        pass

    def type_test(self, type):
        return False

    def parse(self, visitor, caller_type, caller_value, args_type, args):
        return None, None


class ShortcutListCallAppend(ShortcutObjCall):

    def type_test(self, type):
        if type.is_list():
            return True
        return False

    def parse(self, visitor, caller_type, caller_value, args_type, args):
        gen_list.python_list_append(visitor, caller_value, args_type[1], args[1])
        return lang_type.get_none_type(), visitor.get_builder().const_int32(0)


class ShortcutListCallGet(ShortcutObjCall):

    def type_test(self, type):
        if type.is_list():
            return True
        return False

    def parse(self, visitor, caller_type, caller_value, args_type, args):
        item = gen_list.python_list_array_get_item(visitor, caller_type, caller_value, args[1])
        return caller_type.get_content(), item


def get_obj_call_shortcuts(type_to_test, name):
    shortcuts = {
        "append": [ShortcutListCallAppend()],
        "__getitem__": [ShortcutListCallGet()]
    }

    try:
        list_shortcuts = shortcuts[name]
        for e in list_shortcuts:
            if e.type_test(type_to_test):
                return e
    except KeyError:
        return None
    return None
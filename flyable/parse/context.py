import flyable.parse.variable as var


class Context:

    def __init__(self):
        self.__vars = []

    def add_var(self, name, type):
        new_var = var.Variable(len(self.__vars))
        new_var.set_name(name)
        new_var.set_type(type)
        self.__vars.append(new_var)
        return new_var

    def get_var(self, index):
        if isinstance(index, str):  # search by name
            for e in self.__vars:
                if e.get_name() == str:
                    return e
        else:  # search by index
            return self.__vars[index]

    def find_active_var(self, name):
        for e in self.__vars:
            if e.get_name() == name and e.is_used():
                return e
        return None

    def vars_iter(self):
        return iter(self.__vars)

    def get_vars_count(self):
        return len(self.__vars)

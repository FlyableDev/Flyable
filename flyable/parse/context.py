from flyable.data.lang_type import LangType
from flyable.parse.variable import Variable


class Context:

    def __init__(self):
        self.__vars: list[Variable] = []

    def add_var(self, name: str, type: LangType):
        new_var = Variable(len(self.__vars))
        new_var.set_name(name)
        new_var.set_type(type)
        new_var.set_context(self)
        self.__vars.append(new_var)
        return new_var

    def get_var(self, value: str | int) -> Variable | None:
        if isinstance(value, str):  # search by name
            return self.get_var_by_name(value)
        else:  # search by index
            return self.get_var_by_id(value)

    def get_var_by_id(self, id: int) -> Variable | None:
        return self.__vars[id]

    def get_var_by_name(self, name: str) -> Variable | None:
        """Finds the variable with the matching name

        Args:
            name (str): the name of the variable
        Returns:
             Union[var.Variable, None]: the variable with matching name
             or none if it doesn't find it
        """
        for var in self.__vars:
            if var.get_name() == name:
                return var
        return None

    def find_active_var(self, name: str):
        for var in self.__vars:
            if var.get_name() == name and var.is_used():
                return var
        return None

    def vars_iter(self):
        return iter(self.__vars)

    def get_vars_count(self):
        return len(self.__vars)

    def clear_info(self):
        for var in self.__vars:
            var.set_use(True)

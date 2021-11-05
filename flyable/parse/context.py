from typing import Union
import flyable.parse.variable as var

class Context:

    def __init__(self):
        self.__vars: list[var.Variable] = []

    def add_var(self, name, type):
        new_var = var.Variable(len(self.__vars))
        new_var.set_name(name)
        new_var.set_type(type)
        self.__vars.append(new_var)
        return new_var

    def get_var(self, value: Union[str, int]) -> Union[var.Variable, None]:
        """
        Deprecated: you should call `get_var_by_idx` or `get_var_by_name` instead
        """
        if isinstance(value, str):  # search by name
            return self.get_var_by_name(value)
        else:  # search by index
            return self.get_var_by_idx(value)
        
    def get_var_by_idx(self, idx: int) -> Union[var.Variable, None]:
        """Finds the variable at the matching index

        Args:
            idx (int): the index where the variable is

        Returns:
            Union[var.Variable, None]: the variable or None if the index is out of bounds
        """
        return self.__vars[idx] if abs(idx) < len(self.__vars) else None 
        
    
    def get_var_by_name(self, name: str) -> Union[var.Variable, None]:
        """Finds the variable with the matching name

        Args:
            name (str): 
        Returns:
             Union[var.Variable, None]: the variable or none if it doesn't find it
        """
        for var in self.__vars:
            if var.get_name() == name:
                return var
        return None

    def find_active_var(self, name):
        for e in self.__vars:
            if e.get_name() == name and e.is_used():
                return e
        return None

    def vars_iter(self):
        return iter(self.__vars)

    def get_vars_count(self):
        return len(self.__vars)

from flyable.data.error import Error


class ErrorThrower:

    def __init__(self):
        self.__errors: list[Error] = []

    @property
    def has_error(self):
        return len(self.__errors) > 0

    def throw_error(self, msg: str, line: int, row: int):
        self.__errors.append(Error(msg, line, row))

    def throw_errors(self, errors: list[Error]):
        self.__errors = errors.copy()

    def get_error(self, index: int):
        return self.__errors[index]

    def get_errors_count(self):
        return len(self.__errors)

    def get_errors(self):
        return self.__errors.copy()

    def errors_iter(self):
        return iter(self.__errors)

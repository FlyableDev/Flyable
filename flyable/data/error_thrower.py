from flyable.data.error import Error


class ErrorThrower:

    def __init__(self):
        self.__errors: list[Error] = []

    def throw_error(self, msg: str, line: int | None, row: int | None):
        self.__errors.append(Error(msg, line if line is not None else -1, row if row is not None else -1))

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

    def has_error(self):
        return len(self.__errors) > 0

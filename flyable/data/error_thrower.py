import flyable.data.error as err


class ErrorThrower:

    def __init__(self):
        self.__errors = []

    def throw_error(self, msg, line, row):
        self.__errors.append(err.Error(msg, line, row))

    def throw_errors(self, errors):
        self.__errors = errors.copy()

    def get_error(self, index):
        return self.__errors

    def get_errors_count(self):
        return len(self.__errors)

    def get_errors(self):
        return self.__errors.copy()

    def has_error(self):
        return len(self.__errors) > 0

    def errors_iter(self):
        return iter(self.__errors)

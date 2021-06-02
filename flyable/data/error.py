class Error:

    def __init__(self, message="", line=0, row=0):
        self.__message = message
        self.__line = line
        self.__row = row

    def set_message(self, message):
        self.__message = message

    def get_message(self):
        return self.__message

    def set_line(self, line):
        self.__line = line

    def get_line(self):
        return self.__line

    def set_row(self, row):
        self.__row = row

    def get_row(self):
        return self.__row

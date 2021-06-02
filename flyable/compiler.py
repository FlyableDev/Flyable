import flyable.parse.parser as par
from flyable.parse.pre_parser import PreParser
from flyable.data import lang_file, comp_data
from flyable.data.error_thrower import ErrorThrower
from flyable.code_gen.code_gen import CodeGen
from flyable.data.lang_func_impl import LangFuncImpl


class Compiler(ErrorThrower):

    def __init__(self):
        self.__data = comp_data.CompData()
        self.__parser = par.Parser()

    def add_file(self, path):
        new_file = lang_file.LangFile()
        new_file.read_from_path(path)
        self.__data.add_file(new_file)

    def compile(self, ):
        self.__pre_parse()

        if self.has_error() == False:
            self.__parse()

        if self.has_error() == False:
            self.__code_gen()

        self.throw_errors(self.__parser.get_errors())

        for e in self.errors_iter():
            print("" + e.get_message() + " " + str(e.get_line()) + " " + str(e.get_row()))

    def __pre_parse(self):
        pre_parser = PreParser(self.__data)
        pre_parser.parse(self.__data)
        self.throw_errors(pre_parser.get_errors())

    def __parse(self):
        for i in range(self.__data.get_files_count()):
            file = self.__data.get_file(i)
            self.__parser.parse_file(file)

        for i in range(self.__data.get_funcs_count()):
            func = self.__data.get_func(i)
            self.__parser.parse_func(self.__data, func)

        for i in range(self.__data.get_classes_count()):
            lang_class = self.__data.get_class(i)
            self.__parser.parse_class(lang_class)

        self.__parse_main()

        self.throw_errors(self.__parser.get_errors())

    def __code_gen(self):
        code_gen = CodeGen()
        code_gen.generate(self.__data)

    def __parse_main(self):
        main_func = self.__data.find_main()
        if main_func is not None:
            main_impl = LangFuncImpl()
            main_func.add_impl(main_impl)
            self.__parser.parse_impl(self.__data, main_impl)
        else:
            self.throw_error("No main function found with no arguments", 0, 0)

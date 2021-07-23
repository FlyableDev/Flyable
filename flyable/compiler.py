import flyable.parse.parser as par
from flyable.parse.pre_parser import PreParser
from flyable.data import lang_file, comp_data
from flyable.data.error_thrower import ErrorThrower
from flyable.code_gen.code_gen import CodeGen
from flyable.data.lang_func_impl import LangFuncImpl
import flyable.code_gen.code_gen as gen
import flyable.parse.adapter as adapter
import flyable.data.lang_class as lang_class


class Compiler(ErrorThrower):

    def __init__(self):
        self.__data = comp_data.CompData()
        self.set_output_path("output.o")
        self.__code_gen = gen.CodeGen(self.__data)
        self.__code_gen.setup()
        self.__parser = par.Parser(self.__data, self.__code_gen)

    def add_file(self, path):
        new_file = lang_file.LangFile()
        new_file.read_from_path(path)
        self.__data.add_file(new_file)

    def set_output_path(self, path):
        self.__data.set_config("output", path)

    def compile(self):
        self.__pre_parse()

        if not self.has_error():
            self.__parse()

        self.throw_errors(self.__parser.get_errors())

        for e in self.errors_iter():
            print("" + e.get_message() + " " + str(e.get_line()) + " " + str(e.get_row()))

        if not self.has_error():
            self.__code_gen.setup_struct()
            self.__code_gen.generate_main()
            self.__code_gen.write()

    def __pre_parse(self):
        pre_parser = PreParser(self.__data, self.__code_gen)
        pre_parser.parse(self.__data)
        self.__resolve_inheritance()
        self.throw_errors(pre_parser.get_errors())

    def __parse(self):
        code_gen = CodeGen(self.__data)

        # Parse the code until it the compiler stop finding new data
        while True:
            self.__data.set_changed(False)
            self.__data.clear_info()
            code_gen.clear()
            code_gen.setup()

            try:
                adapter.adapt_func(self.__data.get_file(0).get_global_func(), [], self.__data, self.__parser)
            except Exception as exception:
                if not self.__parser.has_error():  # If there is no error we launch the exception as a failure
                    raise exception
                break

            if self.__parser.has_error() or not self.__data.is_changed():
                break

        self.throw_errors(self.__parser.get_errors())

    def __resolve_inheritance(self):
        for _class in self.__data.classes_iter():
            node = _class.get_node()
            for e in node.bases:
                found_class = _class.get_file().find_content(e.id)
                if isinstance(found_class, lang_class.LangClass):
                    _class.add_inherit(found_class)
                else:
                    self.__parser.throw_errors(str(e) + " not expected to inherits", node.lineno, node.end_col_offset)

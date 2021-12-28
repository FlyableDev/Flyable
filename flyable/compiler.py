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
        super().__init__()
        self.__data: comp_data.CompData = comp_data.CompData()
        self.set_output_path("output.o")
        self.__code_gen: CodeGen = gen.CodeGen(self.__data)
        self.__code_gen.setup()
        self.__parser: par.Parser = par.Parser(self.__data, self.__code_gen)
        self.__main_impl = None

    def add_file(self, path: str):
        new_file: lang_file.LangFile = lang_file.LangFile()
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
            print(f"{e.message} [{e.line}, {e.row}]")

        if not self.has_error():
            self.__code_gen.setup_struct()
            self.__code_gen.generate_main(self.__main_impl)
            self.__code_gen.write()

    def __pre_parse(self):
        pre_parser = PreParser(self.__data, self.__code_gen)
        pre_parser.parse(self.__data)
        self.__resolve_inheritance()
        self.throw_errors(pre_parser.get_errors())

    def __parse(self):
        self.__pre_parse()
        code_gen = self.__code_gen

        # Parse the code until it the compiler stop finding new data
        while True:
            self.__data.clear_info()
            code_gen.clear()
            code_gen.setup()
            self.__data.set_changed(False)

            try:

                # Create a specialization for the main module to execute
                self.__main_impl = adapter.adapt_func(self.__data.get_file(0).get_global_func(), [], self.__data,
                                                      self.__parser)

                # Then generate an implementation for all python methods / funcs
                adapter.adapt_all_python_impl(self.__data, self.__parser)

            except Exception as exception:
                if not self.__parser.has_error():  # If there is no error we launch the exception as a failure
                    raise exception
                break

            # If there is an error or no compiler data has been modifier we're confident that the generate code is valid
            if self.__parser.has_error() or not self.__data.is_changed():
                break
            else:
                self.__data.increment_current_iteration()

        self.throw_errors(self.__parser.get_errors())

    def __resolve_inheritance(self):
        for _class in self.__data.classes_iter():
            node = _class.get_node()
            for e in node.bases:
                found_class = _class.get_file().find_content_by_id(e.id)
                if isinstance(found_class, lang_class.LangClass):
                    _class.add_inherit(found_class)
                else:
                    self.__parser.throw_error(str(e) + " not expected to inherits", node.lineno, node.end_col_offset)

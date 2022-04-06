from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from flyable.data.comp_data import CompData
    from flyable.parse.parser import Parser

import flyable.code_gen.code_gen as gen
import flyable.parse.parser as par
from flyable.code_gen.code_gen import CodeGen
from flyable.data import comp_data, lang_file
from flyable.data.error_thrower import ErrorThrower


class Compiler(ErrorThrower):
    def __init__(self):
        super().__init__()
        self._data: CompData = comp_data.CompData()
        self.set_output_path("output.o")
        self._code_gen: CodeGen = gen.CodeGen(self._data)
        self._code_gen.setup()
        self._parser: Parser = par.Parser(self._data, self._code_gen)

    def add_file(self, path: str):
        new_file: lang_file.LangFile = lang_file.LangFile()
        new_file.read_from_path(path)
        self._data.add_file(new_file)

    def set_output_path(self, path):
        self._data.set_config("output", path)

    def compile(self):

        self.__parse()

        self.throw_errors(self._parser.get_errors())

        for e in self.errors_iter():
            print(f"{e.message} [{e.line}, {e.row}]")

        if not self.has_error():
            self._code_gen.generate_main()
            self._code_gen.write()

    def __parse(self):
        code_gen = self._code_gen

        for i in range(self._data.get_files_count()):
            file = self._data.get_file(i)
            self._parser.parse_file(file)

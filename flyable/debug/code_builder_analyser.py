import ast
from typing import Any, Callable

from flyable.code_gen.code_builder import CODE_BUILDER_IDS, CodeBuilder
from flyable.code_gen.code_writer import CodeWriter


class CodeBuilderAnalyser(CodeBuilder):
    def __init__(self, func):
        super().__init__(func)
        self.setup()
        self.__current_method: str = ""
        self.__is_writing_method_id = False
    
    @property
    def __writer(self) -> CodeWriter:
        return getattr(self, "_CodeBuilder__writer")

    def set_insert_block(self, block):
        result = super().set_insert_block(block)
        self.__writer.add_int32 = self.__debug_writer(self.__writer.add_int32)
        return result

    def setup(self, max_depth: int = -1):
        self.max_depth = max_depth
        for method_name in CODE_BUILDER_IDS:
            method = getattr(self, method_name)
            setattr(self, method_name, self.__gen_method(method))
        # setattr(self, method_name, self.__gen_method(getattr(self, method_name)))

    def __gen_method(self, func: Callable) -> Callable:
        def new_method(*args, **kwargs):
            self.__current_method = func.__name__
            self.__is_writing_method_id = True
            result = func(*args, **kwargs)
            print(f"args: {args}")
            print(f"{result=}\n")
            return result

        return new_method

    def __debug_writer(self, func_add_int_32):
        def debug_add_int32(value):
            if self.__is_writing_method_id:
                print(f"writing {value} ({self.__current_method})")
                self.__is_writing_method_id = False
            result = func_add_int_32(value)
            return result
        
        return debug_add_int32
    



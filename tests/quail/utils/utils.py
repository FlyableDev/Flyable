from dataclasses import dataclass


class CompilationError(Exception):
    pass


@dataclass
class StdOut:
    content: str = ""
    write_calls: int = 0

    def clear(self):
        self.content = ''
        self.write_calls = 0
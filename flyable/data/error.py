from dataclasses import dataclass


@dataclass
class Error:
    message: str = ""
    line: int = 0
    row: int = 0

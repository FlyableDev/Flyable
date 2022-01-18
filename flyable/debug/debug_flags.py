from enum import Enum, auto


class DebugFlag:
    def __init__(self) -> None:
        pass


class ShowVisitAst(DebugFlag):
    def __init__(self) -> None:
        pass


class DebugFlags(Enum):
    SHOW_VISIT_AST = auto()











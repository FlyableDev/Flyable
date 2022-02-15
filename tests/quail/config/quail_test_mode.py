from enum import Enum, auto


class QuailTestMode(Enum):
    """
    Enum where the different test modes for Quail are defined\n
    - F -> Flyable
    - P -> Python
    """

    FP_STDOUT_COMPARE = auto()
    """Compares the stdout of Flyable and Python"""

    F_STDOUT_ONLY_TRUE = auto()
    """Only looks at the stdout of Flyable, but makes sure that all of it is only composed of True value"""

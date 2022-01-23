__tabs: int = 0


def dprint(*args, sep=" ", end="\n", flush=False, file=None):
    """Emulates the print method but adds the indentation"""
    print("\t" * __tabs, end="")
    print(*args, sep=sep, end=end, file=file, flush=flush)


def ddivider(divider_symbol="-", divider_length=20):
    """"""
    print("\t" * __tabs, end="")
    print(divider_symbol * divider_length)


def dindent_plus(intentation=1):
    global __tabs
    __tabs += intentation


def dindent_minus(intentation=1):
    global __tabs
    __tabs -= intentation


def dset_indent(intentation=0):
    global __tabs
    __tabs = intentation


def dget_indent():
    """Returns the current level of indentation of the debugger"""
    return __tabs
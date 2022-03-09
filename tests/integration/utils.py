class CompilationError(Exception):
    pass

class Style:
    styles = {
        "0": "\033[30m",                # BLACK
        "1": "\033[38;2;0;0;128m",      # DARK_BLUE
        "2": "\033[38;2;0;100;0m",      # DARK_GREEN
        "3": "\033[38;2;0;128;128m",    # DARK_CYAN
        "4": "\033[38;2;200;0;0m",      # DARK_RED
        "5": "\033[38;2;128;0;128m",    # DARK_PURPLE
        "6": "\033[1;33m",              # GOLD
        "7": "\033[0;37m",              # LIGHT_GRAY
        "8": "\033[38;2;25;25;25m",     # DARK_GRAY
        "9": "\033[1;34m",              # BLUE
        "a": "\033[0;32m",              # GREEN
        "b": "\033[1;36m",              # CYAN
        "c": "\033[1;31m",              # RED
        "d": "\033[1;35m",              # LIGHT_PURPLE
        "e": "\033[38;2;255;255;0m",    # YELLOW
        "f": "\033[38;2;255;255;255m",  # WHITE

        "r": '\033[0m',    # RESET
        "l": '\033[1m',    # BOLD
        "n": '\033[4m',    # UNDERLINE
        "o": '\033[3m',    # ITALIC
        "&": "&",          # &
    }
    WARNING = "&e"
    ERROR = "&c"
    OK = "&a"
    PENDING = "&9"

    @staticmethod
    def stylize(msg: str, reset_style=True) -> str:
        msg += "&r" if reset_style else ""
        for pattern, style in Style.styles.items():
            msg = msg.replace("&" + pattern, style)
        return msg

    @staticmethod
    def style_print(*args, sep=' ', end='\n', file=None, reset_style=True):
        args = [Style.stylize(arg, reset_style) if isinstance(arg, str) else arg for arg in args]
        print(*args, sep=sep, end=end, file=file)


from enum import Enum
from typing import Union


class ConsoleColorFlags(Enum):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_fail(*args, sep='', end='\n', file=None):
    print_custom(*args, color=ConsoleColorFlags.FAIL, sep=sep, end=end, file=file)


def print_warn(*args, sep='', end='\n', file=None):
    print_custom(*args, color=ConsoleColorFlags.WARNING, sep=sep, end=end, file=file)


def print_header(*args, sep='', end='\n', file=None):
    print_custom(*args, color=ConsoleColorFlags.HEADER, sep=sep, end=end, file=file)

def print_ok(*args, sep='', end='\n', file=None):
    print_custom(*args, color=ConsoleColorFlags.OKGREEN, sep=sep, end=end, file=file)


def print_ok_blue(*args, sep='', end='\n', file=None):
    print_custom(*args, color=ConsoleColorFlags.OKBLUE, sep=sep, end=end, file=file)


def print_bold(*args, sep='', end='\n', file=None):
    print_custom(*args, color=ConsoleColorFlags.BOLD, sep=sep, end=end, file=file)


def print_underline(*args, sep='', end='\n', file=None):
    print_custom(*args, color=ConsoleColorFlags.UNDERLINE, sep=sep, end=end, file=file)


def print_custom(*args, color: Union[None, ConsoleColorFlags, str] = None, sep='', end='\n', file=None):
    if color is None:
        print(*args, sep=sep, end=end)
        return
    if isinstance(color, ConsoleColorFlags):
        color = color.value
    args = list(args)
    args.insert(0, color)
    args.append(ConsoleColorFlags.ENDC.value)
    print(*args, sep=sep, end=end, file=file)


def c_w(s: str) -> str:
    """
    Color as warning
    """
    return colorize(s, ConsoleColorFlags.WARNING)


def c_f(s: str) -> str:
    """
    Color as failure
    """
    return colorize(s, ConsoleColorFlags.FAIL)


def c_h(s: str) -> str:
    """
    Color as header
    """
    return colorize(s, ConsoleColorFlags.HEADER)


def c_o(s: str) -> str:
    """
    Color as green OK
    """
    return colorize(s, ConsoleColorFlags.OKGREEN)


def c_ob(s: str) -> str:
    """
    Color as blue OK
    """
    return colorize(s, ConsoleColorFlags.OKBLUE)


def c_b(s: str) -> str:
    """
    Color as bold
    """
    return colorize(s, ConsoleColorFlags.BOLD)


def c_u(s: str) -> str:
    """
    Color as underline
    """
    return colorize(s, ConsoleColorFlags.UNDERLINE)


def colorize_warn(s: str) -> str:
    return c_w(s)


def colorize_fail(s: str) -> str:
    return c_f(s)


def colorize_header(s: str) -> str:
    return c_h(s)


def colorize_ok(s: str) -> str:
    return c_o(s)


def colorize_ok_blue(s: str) -> str:
    return c_ob(s)


def colorize_bold(s: str) -> str:
    return c_b(s)


def colorize_underline(s: str) -> str:
    return c_u(s)


def colorize(s: str, color: Union[ConsoleColorFlags, str]) -> str:
    if isinstance(color, ConsoleColorFlags):
        color = color.value
    return color + s + ConsoleColorFlags.ENDC.value

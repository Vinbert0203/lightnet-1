#
#   Logging functionality
#   Copyright EAVISE
#

from enum import IntEnum, Enum

__all__ = ['log', 'Loglvl']


class Loglvl(IntEnum):
    """ Log level """
    ALL         = -1
    NONE        = 999

    DEBUG       = 0
    WARN        = 1
    ERROR       = 2


class ColorCode(Enum):
    """ Color Codes """
    RESET = '\033[00m'
    BOLD = '\033[01m'

    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    WHITE = '\033[37m'


def colorize(msg, color):
    return ColorCode.BOLD.value + color.value + msg + ColorCode.RESET.value


class Logger:
    """ Logger class """
    def __init__(self):
        self.level = Loglvl.WARN
        self.color = True
        self.lvl_msg = ['[DEBUG]', '[WARN] ', '[ERROR]']
        self.lvl_col = [ColorCode.WHITE, ColorCode.YELLOW, ColorCode.RED]

    def __call__(self, lvl, msg, error=None):
        """ Print out log message if lvl is higher than the set Loglvl """
        if lvl >= self.level:
            if lvl < len(self.lvl_msg):
                pre_msg = self.lvl_msg[lvl]
                if self.color:
                    pre_msg = colorize(pre_msg, self.lvl_col[lvl])
            else:
                pre_msg = '       '
            print(f'{pre_msg} {msg}')

        if error is not None:
            raise error


# Create Logger object
try:
    log
except NameError:
    log = Logger()
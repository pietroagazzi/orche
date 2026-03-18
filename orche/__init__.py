from importlib.metadata import version

from . import builtin
from .logger import setup_logger
from .stack import BuiltinCommandType, Stack

__all__ = ["builtin", "setup_logger", "BuiltinCommandType", "Stack"]

__version__ = version("orche")

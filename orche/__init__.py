from importlib.metadata import PackageNotFoundError, version

from . import builtin
from .logger import setup_logger
from .stack import BuiltinCommandType, Stack

__all__ = ["builtin", "setup_logger", "BuiltinCommandType", "Stack"]

try:
    __version__ = version("orche")
except PackageNotFoundError:
    __version__ = "0.0.0"

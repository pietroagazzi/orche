from importlib.metadata import version

from . import builtin
from .logger import setup_logger
from .stack import Stack

__all__ = ["builtin", "setup_logger", "Stack"]

__version__ = version("orche")

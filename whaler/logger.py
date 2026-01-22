"""Logging configuration for Whaler."""

import logging
import sys
from typing import Literal

from rich.logging import RichHandler

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def setup_logger(
    name: str = "whaler",
    level: LogLevel = "INFO",
    colored: bool = True,
) -> logging.Logger:
    """Setup and configure logger.

    Args:
        name: Logger name
        level: Logging level
        colored: Whether to use colored output

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level))

    if colored:
        handler = RichHandler(rich_tracebacks=True, show_time=True, show_path=False)
    else:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

    handler.setLevel(getattr(logging, level))
    logger.addHandler(handler)

    return logger


def get_logger(name: str = "whaler") -> logging.Logger:
    """Get logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)

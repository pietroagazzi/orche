"""Logging configuration for Whaler."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Literal

from rich.logging import RichHandler

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def setup_logger(
    name: str | None = None,
    verbose: bool = False,
) -> logging.Logger:
    """Setup and configure logger.

    Args:
        name: Logger name (None for root logger)
        verbose: Whether to enable verbose logging to console

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture everything at logger level

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Rotating file handler
    # Ensure log directory exists
    log_dir = Path.cwd() / ".whaler" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "whaler.log"

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler in verbose mode
    if verbose:
        console_handler = RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_path=False,
            markup=True,
        )
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)
    else:
        # If not verbose, don't log to console at all
        pass

    return logger


def get_logger(name: str = "whaler") -> logging.Logger:
    """Get logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)

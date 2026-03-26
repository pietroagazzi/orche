"""Tests for logging configuration."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from rich.logging import RichHandler

from orche.logger import get_logger, setup_logger


class TestSetupLogger:
    def test_returns_logger_instance(self) -> None:
        logger = setup_logger(name="test_returns")
        assert isinstance(logger, logging.Logger)
        logger.handlers.clear()

    def test_creates_log_directory(self, tmp_path: Path, monkeypatch: Any) -> None:
        monkeypatch.chdir(tmp_path)
        logger = setup_logger(name="test_creates_dir")
        log_dir = tmp_path / ".orche" / "logs"
        assert log_dir.exists()
        logger.handlers.clear()

    def test_file_handler_attached(self, tmp_path: Path, monkeypatch: Any) -> None:
        monkeypatch.chdir(tmp_path)
        logger = setup_logger(name="test_file_handler")
        file_handlers = [
            h for h in logger.handlers if isinstance(h, RotatingFileHandler)
        ]
        assert len(file_handlers) == 1
        logger.handlers.clear()

    def test_verbose_adds_console_handler(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        monkeypatch.chdir(tmp_path)
        logger = setup_logger(name="test_verbose", verbose=True)
        rich_handlers = [h for h in logger.handlers if isinstance(h, RichHandler)]
        assert len(rich_handlers) == 1
        logger.handlers.clear()

    def test_not_verbose_no_console_handler(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        monkeypatch.chdir(tmp_path)
        logger = setup_logger(name="test_not_verbose", verbose=False)
        rich_handlers = [h for h in logger.handlers if isinstance(h, RichHandler)]
        assert len(rich_handlers) == 0
        logger.handlers.clear()

    def test_idempotent(self, tmp_path: Path, monkeypatch: Any) -> None:
        monkeypatch.chdir(tmp_path)
        logger1 = setup_logger(name="test_idempotent")
        count = len(logger1.handlers)
        logger2 = setup_logger(name="test_idempotent")
        assert len(logger2.handlers) == count
        assert logger1 is logger2
        logger1.handlers.clear()

    def test_permission_error_degrades_gracefully(
        self, tmp_path: Path, monkeypatch: Any, mocker: Any
    ) -> None:
        monkeypatch.chdir(tmp_path)
        mocker.patch.object(Path, "mkdir", side_effect=OSError("Permission denied"))

        logger = setup_logger(name="test_permission")
        # Should have a NullHandler instead of crashing
        null_handlers = [
            h for h in logger.handlers if isinstance(h, logging.NullHandler)
        ]
        assert len(null_handlers) == 1
        logger.handlers.clear()


class TestGetLogger:
    def test_returns_named_logger(self) -> None:
        logger = get_logger("myapp")
        assert logger.name == "myapp"

    def test_default_name(self) -> None:
        logger = get_logger()
        assert logger.name == "orche"

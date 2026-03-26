"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from orche.stack import Stack


@pytest.fixture()
def tmp_compose_file(tmp_path: Path) -> Path:
    """Create a minimal docker-compose.yml in a temp directory."""
    f = tmp_path / "docker-compose.yml"
    f.write_text("services: {}")
    return f


@pytest.fixture()
def make_stack(tmp_path: Path, tmp_compose_file: Path, mocker: Any) -> Any:
    """Factory that returns a Stack with Docker fully mocked."""
    mocker.patch("orche.stack.DockerComposeWrapper")
    mocker.patch("shutil.which", return_value="/usr/bin/docker")

    def _make(name: str = "test-stack", **kwargs: Any) -> Stack:
        return Stack(
            name=name,
            path=tmp_path,
            compose_files=["docker-compose.yml"],
            **kwargs,
        )

    return _make


@pytest.fixture()
def stack(make_stack: Any) -> Stack:
    """A ready-to-use Stack instance with Docker mocked."""
    return make_stack()  # type: ignore[no-any-return]


@pytest.fixture()
def mock_compose(mocker: Any) -> MagicMock:
    """Patch DockerClient and return the compose mock for docker.py tests."""
    mocker.patch("shutil.which", return_value="/usr/bin/docker")
    mock_client = mocker.patch("orche.docker.DockerClient")
    return mock_client.return_value.compose  # type: ignore[no-any-return]

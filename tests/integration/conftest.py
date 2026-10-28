"""Fixtures for tests that run against a real Docker daemon."""

from __future__ import annotations

import shutil
import subprocess
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest

from orche.stack import Stack

COMPOSE = """\
services:
  web:
    image: busybox:1.36
    command: sh -c "mkdir /www && echo ok > /www/index.html && httpd -f -p 8080 -h /www"
    ports:
      - "127.0.0.1::8080"
    healthcheck:
      test: ["CMD", "wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080"]
      interval: 1s
      timeout: 2s
      retries: 10
  worker:
    image: busybox:1.36
    command: sleep 3600
"""


def _docker_available() -> bool:
    if not shutil.which("docker"):
        return False
    result = subprocess.run(
        ["docker", "compose", "version"], capture_output=True, check=False
    )
    return result.returncode == 0


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    skip = pytest.mark.skip(reason="Docker with the compose plugin is not available")
    available = _docker_available()
    for item in items:
        if "integration" in item.keywords and not available:
            item.add_marker(skip)


@pytest.fixture()
def project_dir(tmp_path: Path) -> Path:
    (tmp_path / "docker-compose.yml").write_text(COMPOSE)
    return tmp_path


@pytest.fixture()
def real_stack(project_dir: Path) -> Iterator[Stack]:
    """A Stack on a real compose project, torn down after the test."""
    name = f"orche-it-{uuid.uuid4().hex[:8]}"
    stack = Stack(name=name, path=project_dir, compose_files=["docker-compose.yml"])
    try:
        yield stack
    finally:
        stack.down(volumes=True)

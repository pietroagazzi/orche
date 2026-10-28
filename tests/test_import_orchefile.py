"""Tests for loading an orchefile and the lifetime of its module."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from orche.cli import import_orchefile
from orche.exceptions import OrchefileError

ORCHEFILE = """\
from pathlib import Path

from orche import Stack

stack = Stack(name="t", path=Path(__file__).parent)
{body}
"""


@pytest.fixture(autouse=True)
def isolated_imports(mocker: Any) -> Iterator[None]:
    """Mock Docker and restore sys.modules/sys.path after each test."""
    mocker.patch("orche.stack.DockerComposeWrapper")
    mocker.patch("shutil.which", return_value="/usr/bin/docker")
    modules, path = dict(sys.modules), list(sys.path)
    yield
    sys.modules.clear()
    sys.modules.update(modules)
    sys.path[:] = path


def write_orchefile(directory: Path, body: str = "") -> Path:
    (directory / "docker-compose.yml").write_text("services: {}")
    orchefile = directory / "orchefile.py"
    orchefile.write_text(ORCHEFILE.format(body=body))
    return orchefile


def test_returns_stack(tmp_path: Path) -> None:
    stack = import_orchefile(write_orchefile(tmp_path))
    assert stack.project_name == "t"


def test_handler_can_lazily_import_sibling_module(tmp_path: Path) -> None:
    (tmp_path / "helpers.py").write_text("VALUE = 42\n")
    orchefile = write_orchefile(
        tmp_path,
        "results = []\n"
        "@stack.commands.up\n"
        "def up():\n"
        "    import helpers\n"
        "    results.append(helpers.VALUE)\n",
    )

    stack = import_orchefile(orchefile)
    stack.run("up")

    assert sys.modules["orchefile"].results == [42]


def test_module_stays_importable_by_name_after_load(tmp_path: Path) -> None:
    orchefile = write_orchefile(
        tmp_path,
        "@stack.commands.up\n"
        "def up():\n"
        "    import orchefile\n"
        "    orchefile.ran = True\n",
    )

    stack = import_orchefile(orchefile)
    stack.run("up")

    assert sys.modules["orchefile"].ran is True


def test_failed_load_leaves_no_trace(tmp_path: Path) -> None:
    orchefile = write_orchefile(tmp_path, "raise RuntimeError('boom')")
    path_before = list(sys.path)

    with pytest.raises(OrchefileError, match="boom"):
        import_orchefile(orchefile)

    assert "orchefile" not in sys.modules
    assert sys.path == path_before


def test_missing_stack_variable_leaves_no_trace(tmp_path: Path) -> None:
    orchefile = tmp_path / "orchefile.py"
    orchefile.write_text("x = 1\n")
    path_before = list(sys.path)

    with pytest.raises(OrchefileError, match="must define a 'stack'"):
        import_orchefile(orchefile)

    assert "orchefile" not in sys.modules
    assert sys.path == path_before

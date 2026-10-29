"""End-to-end tests against a real Docker daemon.

Run with ``pytest -m integration``; they are excluded from the default run.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from click.testing import CliRunner

from orche.cli import main
from orche.exceptions import DockerComposeError
from orche.stack import Stack

pytestmark = pytest.mark.integration


def _running_services(stack: Stack) -> set[str]:
    return {
        c.config.labels["com.docker.compose.service"]
        for c in stack.client().ps()
        if c.state.running
    }


def test_profiles_and_env_files_in_compose_config(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ORCHE_TEST_IMAGE", raising=False)
    (project_dir / "docker-compose.yml").write_text(
        "services:\n  app:\n    image: ${ORCHE_TEST_IMAGE}\n    profiles: [tools]\n"
    )
    (project_dir / "base.env").write_text("ORCHE_TEST_IMAGE=busybox:1.35\n")
    (project_dir / "override.env").write_text("ORCHE_TEST_IMAGE=busybox:1.36\n")
    stack = Stack(
        path=project_dir, profiles=["tools"], env_files=["base.env", "override.env"]
    )
    config = stack.client().compose.config(return_json=True)
    assert isinstance(config, dict)
    assert config["services"]["app"]["image"] == "busybox:1.36"

    monkeypatch.setenv("ORCHE_TEST_IMAGE", "busybox:latest")
    config = stack.client().compose.config(return_json=True)
    assert isinstance(config, dict)
    assert config["services"]["app"]["image"] == "busybox:latest"

    without_profile = Stack(path=project_dir, env_files=["base.env", "override.env"])
    config = without_profile.client().compose.config(return_json=True)
    assert isinstance(config, dict)
    assert not config.get("services")


def test_up_waits_for_healthy_and_down_removes(real_stack: Stack) -> None:
    real_stack.up()
    assert _running_services(real_stack) == {"web", "worker"}

    real_stack.down()
    assert real_stack.client().ps() == []


def test_up_single_service(real_stack: Stack) -> None:
    real_stack.up(services=["worker"])
    assert _running_services(real_stack) == {"worker"}


def test_stop_keeps_containers(real_stack: Stack) -> None:
    real_stack.up()
    real_stack.stop(services=["worker"])

    assert _running_services(real_stack) == {"web"}
    assert len(real_stack.client().compose.ps(all=True)) == 2


def test_rm_single_service_leaves_others(real_stack: Stack) -> None:
    real_stack.up()
    real_stack.rm(services=["worker"])

    assert _running_services(real_stack) == {"web"}
    assert len(real_stack.client().compose.ps(all=True)) == 1


def test_unknown_service_raises_docker_error(real_stack: Stack) -> None:
    with pytest.raises(DockerComposeError):
        real_stack.up(services=["does-not-exist"])


def test_invalid_image_build_failure_is_translated(project_dir: Path) -> None:
    (project_dir / "docker-compose.yml").write_text(
        "services:\n  app:\n    build:\n      context: ./missing\n"
    )
    stack = Stack(
        name=f"orche-it-{uuid.uuid4().hex[:8]}",
        path=project_dir,
        compose_files=["docker-compose.yml"],
    )
    with pytest.raises(DockerComposeError):
        stack.build()


def test_cli_chained_commands(project_dir: Path) -> None:
    name = f"orche-it-{uuid.uuid4().hex[:8]}"
    orchefile = project_dir / "orchefile.py"
    orchefile.write_text(
        "from orche import Stack\n"
        f"stack = Stack(name={name!r}, path={str(project_dir)!r})\n"
        "@stack.commands.up\n"
        "def up():\n"
        "    stack.up()\n"
        "@stack.commands.down\n"
        "def down():\n"
        "    stack.down(volumes=True)\n"
    )
    runner = CliRunner()
    try:
        result = runner.invoke(main, ["-f", str(orchefile), "up", "worker"])
        assert result.exit_code == 0, result.output
    finally:
        result = runner.invoke(main, ["-f", str(orchefile), "down"])
        assert result.exit_code == 0, result.output

"""Tests for DockerComposeWrapper."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from python_on_whales import DockerException

from orche.docker import DockerComposeWrapper
from orche.exceptions import ConfigError, DockerComposeError


@pytest.fixture()
def wrapper(tmp_path: Path, mock_compose: MagicMock) -> DockerComposeWrapper:
    """Create a DockerComposeWrapper with mocked Docker."""
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text("services: {}")
    return DockerComposeWrapper(compose_files=[compose_file])


class TestDockerInit:
    def test_no_docker_raises_docker_compose_error(
        self, tmp_path: Path, mocker: Any
    ) -> None:
        mocker.patch("shutil.which", return_value=None)
        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text("services: {}")

        with pytest.raises(DockerComposeError, match="Docker executable not found"):
            DockerComposeWrapper(compose_files=[compose_file])

    def test_empty_compose_files_raises_config_error(self, mocker: Any) -> None:
        mocker.patch("shutil.which", return_value="/usr/bin/docker")
        with pytest.raises(ConfigError, match="cannot be empty"):
            DockerComposeWrapper(compose_files=[])

    def test_creates_client_with_compose_files(
        self, tmp_path: Path, mocker: Any
    ) -> None:
        mocker.patch("shutil.which", return_value="/usr/bin/docker")
        mock_client = mocker.patch("orche.docker.DockerClient")
        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text("services: {}")

        DockerComposeWrapper(compose_files=[compose_file])
        mock_client.assert_called_once()


class TestDockerBuild:
    def test_build_calls_compose(self, wrapper: DockerComposeWrapper) -> None:
        wrapper.build()
        wrapper.compose.build.assert_called_once_with(services=None)  # type: ignore[attr-defined]

    def test_build_with_services(self, wrapper: DockerComposeWrapper) -> None:
        wrapper.build(services=["web"])
        wrapper.compose.build.assert_called_once_with(services=["web"])  # type: ignore[attr-defined]

    def test_build_docker_exception_raises(self, wrapper: DockerComposeWrapper) -> None:
        wrapper.compose.build.side_effect = DockerException(  # type: ignore[attr-defined]
            command_launched=["build"], return_code=1
        )
        with pytest.raises(DockerComposeError, match="Build failed"):
            wrapper.build()


class TestDockerUp:
    def test_up_calls_compose(self, wrapper: DockerComposeWrapper) -> None:
        wrapper.up()
        wrapper.compose.up.assert_called_once_with(  # type: ignore[attr-defined]
            services=None, detach=True, wait=False
        )

    def test_up_passes_parameters(self, wrapper: DockerComposeWrapper) -> None:
        wrapper.up(services=["web"], detach=False, wait=True)
        wrapper.compose.up.assert_called_once_with(  # type: ignore[attr-defined]
            services=["web"], detach=False, wait=True
        )

    def test_up_docker_exception_raises(self, wrapper: DockerComposeWrapper) -> None:
        wrapper.compose.up.side_effect = DockerException(  # type: ignore[attr-defined]
            command_launched=["up"], return_code=1
        )
        with pytest.raises(DockerComposeError, match="Failed to start"):
            wrapper.up()


class TestDockerDown:
    def test_down_no_services_calls_compose_down(
        self, wrapper: DockerComposeWrapper
    ) -> None:
        wrapper.down()
        wrapper.compose.down.assert_called_once_with(  # type: ignore[attr-defined]
            remove_orphans=True, volumes=False
        )

    def test_down_with_services_calls_stop_then_rm(
        self, wrapper: DockerComposeWrapper
    ) -> None:
        wrapper.down(services=["web"])
        wrapper.compose.stop.assert_called_once_with(["web"])  # type: ignore[attr-defined]
        wrapper.compose.rm.assert_called_once_with(  # type: ignore[attr-defined]
            ["web"], stop=True, volumes=False
        )

    def test_down_docker_exception_raises(self, wrapper: DockerComposeWrapper) -> None:
        wrapper.compose.down.side_effect = DockerException(  # type: ignore[attr-defined]
            command_launched=["down"], return_code=1
        )
        with pytest.raises(DockerComposeError, match="Failed to stop"):
            wrapper.down()


class TestDockerStop:
    def test_stop_calls_compose(self, wrapper: DockerComposeWrapper) -> None:
        wrapper.stop()
        wrapper.compose.stop.assert_called_once_with(services=None)  # type: ignore[attr-defined]

    def test_stop_docker_exception_raises(self, wrapper: DockerComposeWrapper) -> None:
        wrapper.compose.stop.side_effect = DockerException(  # type: ignore[attr-defined]
            command_launched=["stop"], return_code=1
        )
        with pytest.raises(DockerComposeError, match="Failed to stop"):
            wrapper.stop()

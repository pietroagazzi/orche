"""Docker abstraction layer for docker-compose operations."""

import shutil
from collections.abc import Sequence
from pathlib import Path

from python_on_whales import DockerClient, DockerException

from .exceptions import ConfigError, DockerComposeError
from .logger import get_console, get_logger


class DockerComposeWrapper:
    """Abstraction layer for docker-compose operations."""

    def __init__(
        self,
        compose_files: Sequence[str | Path],
        project_name: str | None = None,
        project_path: Path | None = None,
    ):
        """Initialize Docker Compose wrapper.

        Args:
            compose_files: Sequence of docker-compose file paths (str or Path).
                          Files are merged in order. Cannot be empty.
            project_name: Optional project name (defaults to directory name)
            project_path: Optional project path

        Raises:
            ConfigError: If compose_files is empty
        """
        if not compose_files:
            raise ConfigError(
                "compose_files cannot be empty. At least one compose file is required."
            )

        self.compose_files = [Path(cf) for cf in compose_files]
        self.project_name = project_name
        self.project_path = (
            Path(project_path) if project_path else self.compose_files[0].parent
        )

        if not shutil.which("docker"):
            raise DockerComposeError(
                "Docker executable not found. Please ensure Docker is "
                "installed and in your PATH."
            )

        self.compose = DockerClient(
            compose_files=[str(cf) for cf in self.compose_files],
            compose_project_name=project_name,
            compose_project_directory=str(self.project_path),
        ).compose

        self.logger = get_logger("orche.docker")

    def _notice(self, command: str) -> None:
        """Emit a user-visible notice and an internal debug log for a docker command."""
        get_console().print(f"  [dim]$ {command}[/dim]")
        self.logger.debug("Invoking: %s", command)

    def build(self, services: list[str] | None = None) -> None:
        """Build services defined in compose file.

        Args:
            services: Optional list of specific services to build

        Raises:
            DockerComposeError: If build command fails
        """
        parts = ["docker", "compose", "build"]
        if services:
            parts.extend(services)
        self._notice(" ".join(parts))
        try:
            self.compose.build(services=services)
        except DockerException as e:
            raise DockerComposeError(f"Build failed: {e}") from e
        except Exception as e:
            raise DockerComposeError(f"Unexpected error during build: {e}") from e

    def up(
        self,
        services: list[str] | None = None,
        detach: bool = True,
        wait: bool = False,
    ) -> None:
        """Start services.

        Args:
            services: Optional list of specific services to start
            detach: Run containers in background (default: True)
            wait: Wait for services to be running (default: False)

        Raises:
            DockerComposeError: If up command fails
        """
        parts = ["docker", "compose", "up"]
        if detach:
            parts.append("--detach")
        if wait:
            parts.append("--wait")
        if services:
            parts.extend(services)
        self._notice(" ".join(parts))
        try:
            self.compose.up(services=services, detach=detach, wait=wait)
        except DockerException as e:
            raise DockerComposeError(f"Failed to start services: {e}") from e
        except Exception as e:
            raise DockerComposeError(f"Unexpected error during up: {e}") from e

    def down(
        self,
        services: list[str] | None = None,
        remove_orphans: bool = True,
        volumes: bool = False,
    ) -> None:
        """Stop and remove services.

        Args:
            services: Optional list of specific services to stop and remove
            remove_orphans: Remove containers for services not in compose file
            volumes: Remove named volumes declared in the volumes section

        Raises:
            DockerComposeError: If down command fails
        """
        try:
            if services:
                stop_parts = ["docker", "compose", "stop", *services]
                self._notice(" ".join(stop_parts))
                self.compose.stop(services)
                rm_parts = [
                    "docker",
                    "compose",
                    "rm",
                    "--stop",
                    *(["--volumes"] if volumes else []),
                    *services,
                ]
                self._notice(" ".join(rm_parts))
                self.compose.rm(services, stop=True, volumes=volumes)
            else:
                down_parts = ["docker", "compose", "down", "--remove-orphans"]
                if volumes:
                    down_parts.append("--volumes")
                self._notice(" ".join(down_parts))
                self.compose.down(remove_orphans=remove_orphans, volumes=volumes)
        except DockerException as e:
            raise DockerComposeError(f"Failed to stop services: {e}") from e
        except Exception as e:
            raise DockerComposeError(f"Unexpected error during down: {e}") from e

    def stop(self, services: list[str] | None = None) -> None:
        """Stop services without removing them.

        Args:
            services: Optional list of specific services to stop

        Raises:
            DockerComposeError: If stop command fails
        """
        parts = ["docker", "compose", "stop"]
        if services:
            parts.extend(services)
        self._notice(" ".join(parts))
        try:
            self.compose.stop(services=services)
        except DockerException as e:
            raise DockerComposeError(f"Failed to stop services: {e}") from e
        except Exception as e:
            raise DockerComposeError(f"Unexpected error during stop: {e}") from e

    def ps(self) -> list:
        """Return running containers for this compose project."""
        try:
            return self.compose.ps()
        except Exception as e:
            self.logger.debug("ps() failed: %s", e)
            return []

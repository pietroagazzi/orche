"""Docker abstraction layer for docker-compose operations."""

import shutil
from collections.abc import Sequence
from pathlib import Path

from python_on_whales import DockerClient, DockerException

from .exceptions import DockerComposeError


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
            ValueError: If compose_files is empty
        """
        if not compose_files:
            raise ValueError(
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

    def build(self, services: list[str] | None = None) -> None:
        """Build services defined in compose file.

        Args:
            services: Optional list of specific services to build

        Raises:
            DockerComposeError: If build command fails
        """
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
        try:
            self.compose.up(
                services=services,
                detach=detach,
                wait=wait,
            )
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
                self.compose.stop(services)
                self.compose.rm(services, stop=True, volumes=volumes)
            else:
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
        try:
            self.compose.stop(services=services)
        except DockerException as e:
            raise DockerComposeError(f"Failed to stop services: {e}") from e
        except Exception as e:
            raise DockerComposeError(f"Unexpected error during stop: {e}") from e

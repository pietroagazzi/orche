"""Docker abstraction layer for docker-compose operations."""

import math
import shutil
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

from python_on_whales import DockerClient, DockerException

from .exceptions import ConfigError, DockerComposeError
from .logger import get_console, get_logger


@contextmanager
def _translate_errors(failure: str, operation: str) -> Iterator[None]:
    """Re-raise any error from a docker call as ``DockerComposeError``.

    Args:
        failure: Message prefix used for errors reported by Docker itself
        operation: Operation name used for unexpected, non-Docker errors
    """
    try:
        yield
    except DockerException as e:
        raise DockerComposeError(f"{failure}: {e}") from e
    except Exception as e:
        raise DockerComposeError(f"Unexpected error during {operation}: {e}") from e


class DockerComposeWrapper:
    """Abstraction layer for docker-compose operations."""

    def __init__(
        self,
        compose_files: Sequence[str | Path],
        project_name: str | None = None,
        project_path: Path | None = None,
        profiles: Sequence[str] | None = None,
        env_files: Sequence[str | Path] | None = None,
    ):
        """Initialize Docker Compose wrapper.

        Args:
            compose_files: Sequence of docker-compose file paths (str or Path).
                          Files are merged in order. Cannot be empty.
            project_name: Optional project name (defaults to directory name)
            project_path: Optional project path
            profiles: Compose profiles to enable
            env_files: Ordered Compose interpolation env files

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
            compose_profiles=list(profiles or []),
            compose_env_files=[str(p) for p in (env_files or [])],
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
        with _translate_errors("Build failed", "build"):
            self.compose.build(services=services)

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
        with _translate_errors("Failed to start services", "up"):
            self.compose.up(services=services, detach=detach, wait=wait)

    def down(
        self,
        remove_orphans: bool = True,
        volumes: bool = False,
    ) -> None:
        """Stop and remove the whole project, including its networks.

        Like ``docker compose down``, this always acts on the entire project.
        Use :meth:`rm` to remove specific services.

        Args:
            remove_orphans: Remove containers for services not in compose file
            volumes: Remove named volumes declared in the volumes section

        Raises:
            DockerComposeError: If down command fails
        """
        parts = ["docker", "compose", "down"]
        if remove_orphans:
            parts.append("--remove-orphans")
        if volumes:
            parts.append("--volumes")
        self._notice(" ".join(parts))
        with _translate_errors("Failed to stop services", "down"):
            self.compose.down(remove_orphans=remove_orphans, volumes=volumes)

    def rm(
        self,
        services: list[str] | None = None,
        volumes: bool = False,
    ) -> None:
        """Stop and remove service containers, leaving networks in place.

        Args:
            services: Optional list of specific services to remove
            volumes: Remove anonymous volumes attached to the containers

        Raises:
            DockerComposeError: If rm command fails
        """
        parts = ["docker", "compose", "rm", "--stop", "--force"]
        if volumes:
            parts.append("--volumes")
        if services:
            parts.extend(services)
        self._notice(" ".join(parts))
        with _translate_errors("Failed to remove services", "rm"):
            self.compose.rm(services, stop=True, volumes=volumes)

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
        with _translate_errors("Failed to stop services", "stop"):
            self.compose.stop(services=services)

    def ps(self) -> list:
        """Return running containers for this compose project."""
        try:
            return self.compose.ps()
        except Exception as e:
            self.logger.debug("ps() failed: %s", e)
            return []

    def wait_for_service(
        self, service: str, timeout: float = 60, interval: float = 1
    ) -> None:
        """Wait until every container of a service is running and healthy."""
        if not service.strip():
            raise ConfigError("Service name cannot be empty")
        for name, value in (("timeout", timeout), ("interval", interval)):
            if not math.isfinite(value) or value <= 0:
                raise ConfigError(f"{name} must be a positive finite number")

        deadline = time.monotonic() + timeout
        while True:
            # Fetch fresh Container objects on every poll: their inspected state
            # is cached by python-on-whales.
            with _translate_errors("Failed to inspect service", "service inspection"):
                containers = self.compose.ps(services=[service], all=True)
                states = [container.state for container in containers]

            for state in states:
                if state.status in {"exited", "dead"}:
                    raise DockerComposeError(
                        f"Service '{service}' has a {state.status} container "
                        f"(exit code {state.exit_code})"
                    )
                if state.status == "running" and state.health is None:
                    raise DockerComposeError(
                        f"Service '{service}' has a running container "
                        "without a healthcheck"
                    )
            if states and all(
                s.status == "running"
                and s.health is not None
                and s.health.status == "healthy"
                for s in states
            ):
                return
            reason = (
                "not all containers are healthy" if states else "no containers found"
            )

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise DockerComposeError(
                    f"Timed out waiting for service '{service}' to be healthy "
                    f"after {timeout:g}s ({reason})"
                )
            time.sleep(min(interval, remaining))

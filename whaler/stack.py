"""Main Stack class for orchestrating Docker Compose stacks."""

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Generic, Literal, TypeVar

from dotenv import load_dotenv

from .docker import DockerComposeWrapper
from .logger import get_logger

CommandType = Literal["up", "build", "down", "stop"]
T = TypeVar("T", bound=Callable[[], None])


class CommandRegistry(Generic[T]):
    """Registry for stack commands."""

    def __init__(self) -> None:
        self._commands: dict[str, Callable[[], None]] = {}

    def register(self, name: str) -> Callable[[T], T]:
        """Decorator to register a command."""

        def decorator(func: T) -> T:
            self._commands[name] = func  # type: ignore[assignment]
            return func

        return decorator

    @property
    def up(self) -> Callable[[T], T]:
        """Decorator for the 'up' command."""
        return self.register("up")

    @property
    def down(self) -> Callable[[T], T]:
        """Decorator for the 'down' command."""
        return self.register("down")

    @property
    def build(self) -> Callable[[T], T]:
        """Decorator for the 'build' command."""
        return self.register("build")

    @property
    def stop(self) -> Callable[[T], T]:
        """Decorator for the 'stop' command."""
        return self.register("stop")

    def get(self, name: str) -> Callable[[], None] | None:
        """Get a registered command handler."""
        return self._commands.get(name)


class Stack:
    """Main orchestrator for Docker Compose stacks."""

    def __init__(
        self,
        name: str | None = None,
        path: str | Path = ".",
        compose_file: str | Path = "docker-compose.yml",
        load_env: bool = True,
    ):
        """Initialize a Docker Compose stack.

        Args:
            name: Optional project name (defaults to directory name)
            path: Project root path (defaults to current directory)
            compose_file: Path to docker-compose.yml file (relative to path)
            load_env: Whether to load .env file from project path

        Raises:
            FileNotFoundError: If compose_file does not exist
        """
        self.project_path = Path(path).resolve()
        self.compose_file = self.project_path / compose_file
        self.project_name = name
        self.logger = get_logger()

        # Load .env file if it exists
        if load_env:
            env_file = self.project_path / ".env"
            if env_file.exists():
                load_dotenv(env_file)
                self.logger.debug(f"Loaded environment from {env_file}")

        if not self.compose_file.exists():
            raise FileNotFoundError(
                f"Docker Compose file not found: {self.compose_file}\n"
                f"Please ensure the file exists or provide the correct path."
            )

        # Initialize Docker wrapper
        self._docker = DockerComposeWrapper(
            compose_file=self.compose_file,
            project_name=self.project_name,
            project_path=self.project_path,
        )

        # Command registry
        self.commands: CommandRegistry[Callable[[], None]] = CommandRegistry()

        # Runtime context
        self._active_services: list[str] = []

    def active(self, service: str) -> bool:
        """Check if a service is active in the current execution context.

        If no specific services were requested (empty list),
        all services are considered active.
        """
        if not self._active_services:
            return True
        return service in self._active_services

    def build(self, services: list[str] | None = None) -> "Stack":
        """Build services in the stack.

        If 'services' is not provided, uses the active services from CLI args.

        Args:
            services: Optional list of specific services to build

        Returns:
            Self for method chaining
        """
        target_services = services if services is not None else self._active_services
        if target_services:
            self.logger.info(f"Building services: {', '.join(target_services)}")
        else:
            self.logger.info("Building all services")
        self._docker.build(services=target_services if target_services else None)
        return self

    def up(self, services: list[str] | None = None, wait: bool = True) -> "Stack":
        """Start services in the stack.

        If 'services' is not provided, uses the active services from CLI args.

        Args:
            services: Optional list of specific services to start
            wait: If True, wait for services to be running

        Returns:
            Self for method chaining
        """
        target_services = services if services is not None else self._active_services
        if target_services:
            self.logger.info(f"Starting services: {', '.join(target_services)}")
        else:
            self.logger.info("Starting all services")
        self._docker.up(
            services=target_services if target_services else None, wait=wait
        )
        if wait:
            self.logger.info("Services are ready")
        return self

    def down(self, services: list[str] | None = None, volumes: bool = False) -> "Stack":
        """Stop and remove services in the stack.

        Args:
            services: Optional list of specific services to stop and remove
            volumes: Whether to remove named volumes

        Returns:
            Self for method chaining
        """
        target_services = services if services is not None else self._active_services
        if target_services:
            self.logger.info(
                f"Stopping and removing services: {', '.join(target_services)}"
            )
        else:
            self.logger.info("Stopping and removing all services")

        self._docker.down(
            services=target_services if target_services else None, volumes=volumes
        )
        return self

    def stop(self, services: list[str] | None = None) -> "Stack":
        """Stop services without removing them.

        Args:
            services: Optional list of specific services to stop

        Returns:
            Self for method chaining
        """
        target_services = services if services is not None else self._active_services
        if target_services:
            self.logger.info(f"Stopping services: {', '.join(target_services)}")
        else:
            self.logger.info("Stopping all services")
        self._docker.stop(services=target_services if target_services else None)
        return self

    def run(self) -> None:
        """Parse CLI arguments and execute the requested command."""
        if len(sys.argv) < 2:
            self.logger.info(f"Stack: {self.project_name or 'Whaler'}")
            self.logger.info("\nUsage: python whaler.py <command> [services...]")
            self.logger.info("\nAvailable commands:")
            for cmd in self.commands._commands:
                self.logger.info(f"  - {cmd}")
            sys.exit(1)

        command_name = sys.argv[1]
        self._active_services = sys.argv[2:]

        handler = self.commands.get(command_name)
        if not handler:
            self.logger.error(f"Unknown command '{command_name}'")
            self.logger.info(
                f"Available commands: {', '.join(self.commands._commands.keys())}"
            )
            sys.exit(1)

        try:
            handler()
        except KeyboardInterrupt:
            self.logger.warning("\nInterrupted by user")
            sys.exit(130)
        except Exception as e:
            self.logger.error(f"Command failed: {e}")
            self.logger.debug("Exception details:", exc_info=True)
            sys.exit(1)

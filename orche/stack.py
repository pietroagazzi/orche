"""Main Stack class for orchestrating Docker Compose stacks."""

import socket
from collections.abc import Callable
from pathlib import Path
from typing import Generic, Literal, TypeVar

from rich.panel import Panel
from rich.table import Table

from .docker import DockerComposeWrapper
from .exceptions import CommandError, ConfigError, HookError
from .logger import get_console, get_logger


def _get_local_ip() -> str:
    """Return the local outbound IPv4 address.

    Opens a UDP socket toward 8.8.8.8:80 (no packet is actually sent) to let
    the OS select the correct network interface, then reads the bound address.
    Falls back to `127.0.0.1` if the network is unavailable.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        s.connect(("8.8.8.8", 80))
        ip: str = s.getsockname()[0]
        return ip
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


BuiltinCommandType = Literal["up", "build", "down", "stop"]

T = TypeVar("T", bound=Callable[[], None])


class CommandHandle(Generic[T]):
    """A command slot with optional before/after hooks."""

    def __init__(self, name: str, registry: "CommandRegistry[T]") -> None:
        self._name = name
        self._registry = registry

    def __call__(self, func: T) -> T:
        """Register func as the main handler (backward-compatible decorator)."""
        self._registry._commands[self._name] = func  # type: ignore[assignment]
        return func

    @property
    def before(self) -> Callable[[T], T]:
        """Decorator to register a before-hook for this command."""

        def decorator(func: T) -> T:
            self._registry._before_hooks.setdefault(self._name, []).append(func)  # type: ignore[arg-type]
            return func

        return decorator

    @property
    def after(self) -> Callable[[T], T]:
        """Decorator to register an after-hook for this command."""

        def decorator(func: T) -> T:
            self._registry._after_hooks.setdefault(self._name, []).append(func)  # type: ignore[arg-type]
            return func

        return decorator


class CommandRegistry(Generic[T]):
    """Registry for stack commands."""

    def __init__(self) -> None:
        self._commands: dict[str, Callable[[], None]] = {}
        self._before_hooks: dict[str, list[Callable[[], None]]] = {}
        self._after_hooks: dict[str, list[Callable[[], None]]] = {}

    def register(self, name: str) -> "CommandHandle[T]":
        """Decorator to register a command."""
        return CommandHandle(name, self)

    @property
    def up(self) -> "CommandHandle[T]":
        """Decorator for the 'up' command."""
        return self.register("up")

    @property
    def down(self) -> "CommandHandle[T]":
        """Decorator for the 'down' command."""
        return self.register("down")

    @property
    def build(self) -> "CommandHandle[T]":
        """Decorator for the 'build' command."""
        return self.register("build")

    @property
    def stop(self) -> "CommandHandle[T]":
        """Decorator for the 'stop' command."""
        return self.register("stop")

    def get(self, name: str) -> Callable[[], None] | None:
        """Get a registered command handler."""
        return self._commands.get(name)

    def available_commands(self) -> list[str]:
        """Return list of registered command names."""
        return list(self._commands.keys())

    def get_before_hooks(self, name: str) -> list[Callable[[], None]]:
        """Return before-hooks for the given command."""
        return self._before_hooks.get(name, [])

    def get_after_hooks(self, name: str) -> list[Callable[[], None]]:
        """Return after-hooks for the given command."""
        return self._after_hooks.get(name, [])


class Stack:
    """Main orchestrator for Docker Compose stacks."""

    def __init__(
        self,
        name: str | None = None,
        path: str | Path = ".",
        compose_files: list[str] | list[Path] | None = None,
    ):
        """Initialize a Docker Compose stack.

        Args:
            name: Optional project name (defaults to directory name)
            path: Project root path (defaults to current directory)
            compose_files: List of docker-compose file paths
                          (relative to project path or abs).
                          Files are merged in order (later files override earlier ones).
                          Defaults to ["docker-compose.yml"] if None.
                          Cannot be an empty list.

        Raises:
            ConfigError: If compose_files is empty or files do not exist
        """
        self.project_path: Path = Path(path).resolve()
        self.project_name = name
        self.logger = get_logger()

        compose_file_inputs = (
            ["docker-compose.yml"] if compose_files is None else compose_files
        )
        if not compose_file_inputs:
            raise ConfigError(
                "compose_files cannot be an empty list. "
                "Either omit the parameter to use the default ['docker-compose.yml'], "
                "or provide at least one compose file path."
            )

        self.compose_files = [
            (cf if cf.is_absolute() else self.project_path / cf).resolve()
            for cf in (Path(item) for item in compose_file_inputs)
        ]

        # Validate all compose files exist
        missing_files = [cf for cf in self.compose_files if not cf.exists()]
        if missing_files:
            files_str = "\n  ".join(str(f) for f in missing_files)
            raise ConfigError(
                f"Docker Compose file(s) not found:\n  {files_str}\n"
                f"Please ensure the file(s) exist or provide the correct path(s)."
            )

        # Initialize Docker wrapper
        self._docker = DockerComposeWrapper(
            compose_files=self.compose_files,
            project_name=self.project_name,
            project_path=self.project_path,
        )

        # Command registry
        self.commands: CommandRegistry[Callable[[], None]] = CommandRegistry()

        # Runtime context
        self._active_services: list[str] = []

    def on(self, services: str | list[str]) -> bool:
        """Return True if at least one of the specified services is active.

        This method uses OR logic across the provided service names and checks
        membership against the current execution context (``self._active_services``).

        Args:
            services: A service name or list of service names to check.

        Returns:
            True if any of the specified services are active, False otherwise.
        """
        # Convert single service string to list
        if isinstance(services, str):
            services = [services]

        # If no services specified via CLI, all services are active
        if not self._active_services:
            return True

        # Check if any service in the list is active (OR logic)
        return any(s in self._active_services for s in services)

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

        self._docker.up(services=target_services or None, wait=wait)

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

    def run(self, command: str, services: list[str] | None = None) -> None:
        """Execute a command with before/after hooks.

        Execution order:
            1. Before-hooks run sequentially. First failure raises
               ``HookError`` and aborts (remaining hooks and handler are skipped).
            2. Main handler runs only if all before-hooks succeeded.
               Failures raise ``CommandError``; ``KeyboardInterrupt`` propagates.
            3. After-hooks run sequentially. First failure raises
               ``HookError`` and aborts (remaining after-hooks are skipped).

        Args:
            command: Command name to execute.
            services: List of service names.

        Raises:
            CommandError: If the command is not registered or the handler fails.
            HookError: If a before- or after-hook fails.
        """
        self._active_services = services or []

        handler = self.commands.get(command)
        if not handler:
            available = self.commands.available_commands()
            hint = (
                f" Available: {', '.join(available)}"
                if available
                else " No commands registered — did you forget @stack.commands.up?"
            )
            raise CommandError(f"Unknown command '{command}'.{hint}")

        before_hooks = self.commands.get_before_hooks(command)
        after_hooks = self.commands.get_after_hooks(command)

        # Before-hooks
        for hook in before_hooks:
            try:
                hook()
            except Exception as e:
                raise HookError("before", command, e) from e

        # Main handler
        try:
            handler()
        except Exception as e:
            raise CommandError(f"Command '{command}' failed: {e}") from e

        # After-hooks
        for hook in after_hooks:
            try:
                hook()
            except Exception as e:
                raise HookError("after", command, e) from e

    def client(self) -> DockerComposeWrapper:
        """Get the underlying DockerComposeWrapper instance."""
        return self._docker

    def print_services_summary(self) -> None:
        """Print a Rich panel listing running services and their local URLs."""
        containers = self._docker.ps()
        if not containers:
            return

        local_ip = _get_local_ip()
        console = get_console()

        table = Table(
            show_header=True, header_style="bold cyan", box=None, padding=(0, 2)
        )
        table.add_column("Service", style="bold green")
        table.add_column("Container Port", style="yellow")
        table.add_column("URL", style="blue")

        seen: set[tuple[str, str, str]] = set()
        rows_added = False
        for container in containers:
            service = container.config.labels.get(
                "com.docker.compose.service", container.name
            )
            ports: dict = container.network_settings.ports or {}
            for container_port, bindings in ports.items():
                if not bindings:
                    continue
                for binding in bindings:
                    host_port = binding.get("HostPort", "")
                    if not host_port:
                        continue
                    key = (service, container_port, host_port)
                    if key in seen:
                        continue
                    seen.add(key)
                    port_number = container_port.split("/")[0]
                    scheme = "https" if port_number == "443" else "http"
                    table.add_row(
                        service,
                        container_port,
                        f"{scheme}://{local_ip}:{host_port}",
                    )
                    rows_added = True

        if rows_added:
            console.print(
                Panel(table, title="[bold]Services[/bold]", border_style="cyan")
            )

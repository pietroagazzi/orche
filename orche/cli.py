"""Command-line interface for Orche."""

import importlib.util
import sys
from pathlib import Path

import click
from rich.console import Console

from orche import __version__
from orche.exceptions import CommandError, OrcheError, OrchefileError
from orche.logger import setup_logger
from orche.stack import Stack


def find_or_validate_orchefile(file_path: Path) -> Path:
    """Find orchefile.py or validate custom path.

    Args:
        file_path: Path to orchefile (may be relative or absolute)

    Returns:
        Absolute path to validated orchefile

    Raises:
        OrchefileError: If orchefile is not found
    """
    # Default case: search for orchefile.py in current directory
    if file_path.name == "orchefile.py" and not file_path.is_absolute():
        orchefile = Path.cwd() / "orchefile.py"
        if not orchefile.exists():
            raise OrchefileError(
                f"orchefile.py not found in {Path.cwd()}\n"
                "Make sure you're in a directory with an orchefile.py file."
            )
        return orchefile.resolve()

    # Custom path: validate it exists
    resolved_path = file_path if file_path.is_absolute() else Path.cwd() / file_path
    if not resolved_path.exists():
        raise OrchefileError(f"File not found: {resolved_path}")
    return resolved_path.resolve()


def import_orchefile(orchefile_path: Path) -> Stack:
    """Import orchefile.py as a module and extract stack instance.

    Uses importlib to load the orchefile as a proper Python module,
    similar to how Flask loads app instances.

    Args:
        orchefile_path: Path to orchefile.py

    Returns:
        Stack instance from orchefile

    Raises:
        OrchefileError: If orchefile cannot be loaded or is invalid
    """
    orchefile_dir = orchefile_path.parent.resolve()
    module_name = orchefile_path.stem

    # Temporarily add orchefile directory to sys.path for local imports
    added_to_path = str(orchefile_dir) not in sys.path
    if added_to_path:
        sys.path.insert(0, str(orchefile_dir))

    try:
        spec = importlib.util.spec_from_file_location(module_name, orchefile_path)

        if spec is None or spec.loader is None:
            raise OrchefileError(f"Cannot load module from {orchefile_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            raise OrchefileError(f"Failed to execute orchefile: {e}") from e

        # Extract 'stack' variable (convention-based loading)
        if not hasattr(module, "stack"):
            raise OrchefileError(
                f"Orchefile {orchefile_path} must define a 'stack' variable.\n"
                f"Example: stack = Stack(name='my-stack', "
                "compose_files=['docker-compose.yml'])"
            )

        stack = module.stack
        if not isinstance(stack, Stack):
            raise OrchefileError(
                f"'stack' variable must be a Stack instance, got {type(stack).__name__}"
            )

        return stack
    finally:
        if added_to_path and str(orchefile_dir) in sys.path:
            sys.path.remove(str(orchefile_dir))
        sys.modules.pop(module_name, None)


def _parse_chained(
    command: str, services: tuple[str, ...]
) -> list[tuple[str, list[str]]]:
    """Split a flat token list into chained (command, services) pairs.

    Commas act as separators between invocations, either standalone (`` , ``)
    or attached to the preceding token (``build,``).

    Empty groups produced by leading, trailing, or consecutive commas are
    silently filtered out. As a result, degenerate inputs such as ``orche ,``
    or ``orche ,,`` produce an empty list and no commands are executed. The
    caller is responsible for warning the user when the returned list is empty.

    Examples::

        _parse_chained("build,", ("up", "web"))
        # → [("build", []), ("up", ["web"])]

        _parse_chained("up", ("web,", "build"))
        # → [("up", ["web"]), ("build", [])]

        _parse_chained(",", ("up",))
        # → [("up", [])]  leading comma is dropped, "up" still runs

        _parse_chained(",", (",",))
        # → []  all tokens are commas, nothing to run
    """
    tokens = [command, *services]
    groups: list[list[str]] = []
    current: list[str] = []

    for token in tokens:
        if token == ",":
            groups.append(current)
            current = []
        elif token.endswith(","):
            current.append(token[:-1])
            groups.append(current)
            current = []
        else:
            current.append(token)

    if current:
        groups.append(current)

    return [(g[0], g[1:]) for g in groups if g]


@click.command(
    epilog=(
        "Built-in commands: up, build, down, stop. "
        "Custom commands defined in orchefile.py. "
        "Chain multiple commands with commas: orche build, up web."
    )
)
@click.argument("command")
@click.argument("services", nargs=-1)
@click.option(
    "-f",
    "--file",
    default="orchefile.py",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path to orchefile (default: orchefile.py)",
)
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.version_option(version=__version__, prog_name="orche")
def main(command: str, services: tuple[str, ...], file: Path, debug: bool) -> None:
    """Orche - Docker Compose Stack Orchestrator

    Execute commands defined in your orchefile.py with Docker Compose.
    """
    error_console = Console(stderr=True)

    # Setup logging
    setup_logger(debug=debug)

    # Find and import orchefile
    try:
        orchefile = find_or_validate_orchefile(file)
        stack = import_orchefile(orchefile)
    except OrchefileError as e:
        error_console.print(f"[red]Error: {e}[/red]")
        if debug:
            error_console.print_exception()
        sys.exit(1)

    # Execute each chained invocation sequentially; stop on first failure
    invocations = _parse_chained(command, services)
    if not invocations:
        error_console.print(
            "[yellow]Warning: no commands to run — all tokens were commas. "
            "Did you mean to chain commands, e.g. `orche build, up`?[/yellow]"
        )
        sys.exit(1)
    for cmd, svcs in invocations:
        try:
            stack.run(command=cmd, services=svcs)
        except CommandError as e:
            error_console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
        except OrcheError as e:
            error_console.print(f"[red]Error: {e}[/red]")
            if debug:
                error_console.print_exception()
            sys.exit(1)
        except KeyboardInterrupt:
            error_console.print("\n[yellow]Interrupted by user[/yellow]")
            sys.exit(130)
        except Exception as e:
            error_console.print(f"[red]Unexpected error: {e}[/red]")
            if debug:
                error_console.print_exception()
            sys.exit(1)


if __name__ == "__main__":
    main()

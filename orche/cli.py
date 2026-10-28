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
    similar to how Flask loads app instances. On success the module is left
    in ``sys.modules`` and its directory on ``sys.path``; a failed load
    restores both.

    Args:
        orchefile_path: Path to orchefile.py

    Returns:
        Stack instance from orchefile

    Raises:
        OrchefileError: If orchefile cannot be loaded or is invalid
    """
    orchefile_dir = orchefile_path.parent.resolve()
    module_name = orchefile_path.stem

    added_to_path = str(orchefile_dir) not in sys.path
    if added_to_path:
        sys.path.insert(0, str(orchefile_dir))

    loaded = False
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

        loaded = True
        return stack
    finally:
        # Handlers run after loading and may import the orchefile or its sibling
        # modules lazily, so on success both stay available for the process
        # lifetime. Only a failed load is rolled back.
        if not loaded:
            sys.modules.pop(module_name, None)
            if added_to_path and str(orchefile_dir) in sys.path:
                sys.path.remove(str(orchefile_dir))


def _parse_chained(command: str, args: tuple[str, ...]) -> list[tuple[str, list[str]]]:
    """Split a flat token list into chained (command, args) pairs.

    The args of each pair are the raw tokens that followed the command; the
    stack later splits them into services and options.

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
    tokens = [command, *args]
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
    context_settings={"ignore_unknown_options": True},
    epilog=(
        "Built-in commands: up, build, down, stop, rm. "
        "Custom commands defined in orchefile.py. "
        "Chain multiple commands with commas: orche build, up web. "
        "Options after a command are defined by its handler: orche deploy --env prod."
    ),
)
@click.argument("command")
@click.argument("args", nargs=-1, metavar="[SERVICES_AND_OPTIONS]...")
@click.option(
    "-f",
    "--file",
    default="orchefile.py",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path to orchefile (default: orchefile.py)",
)
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.version_option(version=__version__, prog_name="orche")
def main(command: str, args: tuple[str, ...], file: Path, debug: bool) -> None:
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

    invocations = _parse_chained(command, args)
    if not invocations:
        error_console.print(
            "[yellow]Warning: no commands to run — all tokens were commas. "
            "Did you mean to chain commands, e.g. `orche build, up`?[/yellow]"
        )
        sys.exit(1)

    # Parse every invocation before running any, so a typo in a later option
    # does not surface only after earlier commands have already run.
    # Execute sequentially; stop on first failure.
    try:
        parsed = [(cmd, *stack.parse_args(cmd, tokens)) for cmd, tokens in invocations]
        for cmd, services, options in parsed:
            stack.run(command=cmd, services=services, options=options)
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

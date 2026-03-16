"""Command-line interface for Orche."""

import importlib.util
import sys
from pathlib import Path
from typing import NoReturn

import click
from dotenv import load_dotenv
from rich.console import Console

from orche import __version__
from orche.logger import setup_logger
from orche.stack import CommandType, Stack


def find_or_validate_orchefile(file_path: Path) -> Path:
    """Find orchefile.py or validate custom path.

    Args:
        file_path: Path to orchefile (may be relative or absolute)

    Returns:
        Absolute path to validated orchefile

    Raises:
        FileNotFoundError: If orchefile is not found
    """
    # Default case: search for orchefile.py in current directory
    if file_path.name == "orchefile.py" and not file_path.is_absolute():
        orchefile = Path.cwd() / "orchefile.py"
        if not orchefile.exists():
            raise FileNotFoundError(
                f"orchefile.py not found in {Path.cwd()}\n"
                "Make sure you're in a directory with a orchefile.py file."
            )
        return orchefile

    # Custom path: validate it exists
    resolved_path = file_path if file_path.is_absolute() else Path.cwd() / file_path
    if not resolved_path.exists():
        raise FileNotFoundError(f"File not found: {resolved_path}")
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
        ImportError: If orchefile cannot be imported
        AttributeError: If 'stack' variable not found in module
        TypeError: If 'stack' is not a Stack instance
    """
    # Add orchefile directory to sys.path for local imports
    orchefile_dir = orchefile_path.parent.resolve()
    if str(orchefile_dir) not in sys.path:
        sys.path.insert(0, str(orchefile_dir))

    # Load module from file
    module_name = orchefile_path.stem
    spec = importlib.util.spec_from_file_location(module_name, orchefile_path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {orchefile_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise ImportError(f"Failed to execute orchefile: {e}") from e

    # Extract 'stack' variable (convention-based loading)
    if not hasattr(module, "stack"):
        raise AttributeError(
            f"Orchefile {orchefile_path} must define a 'stack' variable.\n"
            f"Example: stack = Stack(name='my-stack', "
            "compose_files=['docker-compose.yml'])"
        )

    stack = module.stack
    if not isinstance(stack, Stack):
        raise TypeError(
            f"'stack' variable must be a Stack instance, got {type(stack).__name__}"
        )

    return stack


@click.command()
@click.argument("command", type=click.Choice(["up", "build", "down", "stop"]))
@click.argument("services", nargs=-1)
@click.option(
    "-f",
    "--file",
    default="orchefile.py",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path to orchefile (default: orchefile.py)",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose/debug logging")
@click.version_option(version=__version__, prog_name="orche")
def main(
    command: CommandType, services: tuple[str, ...], file: Path, verbose: bool
) -> NoReturn:
    """Orche - Docker Compose Stack Orchestrator

    Execute commands defined in your orchefile.py with Docker Compose.
    """
    error_console = Console(stderr=True)

    # Load environment variables
    load_dotenv()

    # Setup logging
    setup_logger(verbose=verbose)

    # Find orchefile
    try:
        orchefile = find_or_validate_orchefile(file)
    except FileNotFoundError as e:
        error_console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    # Import orchefile and get stack
    try:
        stack = import_orchefile(orchefile)
    except (ImportError, AttributeError, TypeError) as e:
        error_console.print(f"[red]Error loading orchefile: {e}[/red]")
        if verbose:
            error_console.print_exception()
        sys.exit(1)

    # Execute command through stack
    try:
        stack.run(command=command, services=list(services))
        sys.exit(0)
    except SystemExit:
        raise  # Allow stack.run() to control exit codes
    except KeyboardInterrupt:
        error_console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        error_console.print(f"[red]Error executing command: {e}[/red]")
        if verbose:
            error_console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()

"""Command-line interface for Whaler."""

import importlib.util
import sys
from pathlib import Path
from typing import NoReturn

import click
from dotenv import load_dotenv
from rich.console import Console

from whaler import __version__
from whaler.logger import setup_logger
from whaler.stack import CommandType, Stack


def find_or_validate_whalerfile(file_path: Path) -> Path:
    """Find whalerfile.py or validate custom path.

    Args:
        file_path: Path to whalerfile (may be relative or absolute)

    Returns:
        Absolute path to validated whalerfile

    Raises:
        FileNotFoundError: If whalerfile is not found
    """
    # Default case: search for whalerfile.py in current directory
    if file_path.name == "whalerfile.py" and not file_path.is_absolute():
        whaler_file = Path.cwd() / "whalerfile.py"
        if not whaler_file.exists():
            raise FileNotFoundError(
                f"whalerfile.py not found in {Path.cwd()}\n"
                "Make sure you're in a directory with a whalerfile.py file."
            )
        return whaler_file

    # Custom path: validate it exists
    resolved_path = file_path if file_path.is_absolute() else Path.cwd() / file_path
    if not resolved_path.exists():
        raise FileNotFoundError(f"File not found: {resolved_path}")
    return resolved_path.resolve()


def import_whalerfile(whalerfile_path: Path) -> Stack:
    """Import whalerfile.py as a module and extract stack instance.

    Uses importlib to load the whalerfile as a proper Python module,
    similar to how Flask loads app instances.

    Args:
        whalerfile_path: Path to whalerfile.py

    Returns:
        Stack instance from whalerfile

    Raises:
        ImportError: If whalerfile cannot be imported
        AttributeError: If 'stack' variable not found in module
        TypeError: If 'stack' is not a Stack instance
    """
    # Add whalerfile directory to sys.path for local imports
    whaler_dir = whalerfile_path.parent.resolve()
    if str(whaler_dir) not in sys.path:
        sys.path.insert(0, str(whaler_dir))

    # Load module from file
    module_name = whalerfile_path.stem
    spec = importlib.util.spec_from_file_location(module_name, whalerfile_path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {whalerfile_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise ImportError(f"Failed to execute whalerfile: {e}") from e

    # Extract 'stack' variable (convention-based loading)
    if not hasattr(module, "stack"):
        raise AttributeError(
            f"Whalerfile {whalerfile_path} must define a 'stack' variable.\n"
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
    default="whalerfile.py",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path to whalerfile (default: whalerfile.py)",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose/debug logging")
@click.version_option(version=__version__, prog_name="whaler")
def main(
    command: CommandType, services: tuple[str, ...], file: Path, verbose: bool
) -> NoReturn:
    """Whaler - Docker Compose Stack Orchestrator

    Execute commands defined in your whalerfile.py with Docker Compose.
    """
    error_console = Console(stderr=True)

    # Load environment variables
    load_dotenv()

    # Setup logging
    setup_logger(verbose=verbose)

    # Find whalerfile
    try:
        whaler_file = find_or_validate_whalerfile(file)
    except FileNotFoundError as e:
        error_console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    # Import whalerfile and get stack
    try:
        stack = import_whalerfile(whaler_file)
    except (ImportError, AttributeError, TypeError) as e:
        error_console.print(f"[red]Error loading whalerfile: {e}[/red]")
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

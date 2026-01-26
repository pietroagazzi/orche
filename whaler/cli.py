"""Command-line interface for Whaler."""

import argparse
import os
import sys
from pathlib import Path
from typing import Literal, NoReturn

from dotenv import load_dotenv
from rich.console import Console

from whaler import __version__
from whaler.logger import setup_logger

CommandName = Literal["up", "build", "down", "stop"]


def find_whaler_file() -> Path:
    """Find whalefile.py in current directory.

    Returns:
        Path to whalefile.py file

    Raises:
        FileNotFoundError: If whalefile.py is not found
    """
    whaler_file = Path.cwd() / "whalefile.py"
    if not whaler_file.exists():
        raise FileNotFoundError(
            f"whalefile.py not found in {Path.cwd()}\n"
            "Make sure you're in a directory with a whalefile.py file."
        )
    return whaler_file


def execute_whaler_file(
    whaler_file: Path,
    command: str,
    services: list[str],
    verbose: bool = False,
) -> None:
    """Execute whalefile.py file with given command.

    Args:
        whaler_file: Path to whalefile.py file
        command: Command to execute (up, build, down, stop)
        services: List of service names
        verbose: Enable verbose/debug logging
    """
    # Load environment variables from .env file
    load_dotenv()

    # Setup logging based on verbosity
    setup_logger(verbose=verbose)

    # Add current working directory to sys.path to allow local imports
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())

    # Prepare sys.argv for the whalefile.py script
    # This allows the script to access command and services via sys.argv
    original_argv = sys.argv.copy()
    sys.argv = ["whalefile.py", command] + services

    try:
        # Read and execute the whalefile.py file
        with open(whaler_file, encoding="utf-8") as f:
            code = compile(f.read(), str(whaler_file), "exec")
            # Execute in global namespace so imports work correctly
            exec(code, {"__name__": "__main__", "__file__": str(whaler_file)})
    finally:
        # Restore original sys.argv
        sys.argv = original_argv


def main() -> NoReturn:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Whaler - Docker Compose Stack Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  whaler up              Execute whalefile.py with 'up' command
  whaler up api web      Execute whalefile.py with 'up' command for specific services
  whaler build           Execute whalefile.py with 'build' command
  whaler down            Execute whalefile.py with 'down' command
  whaler stop            Execute whalefile.py with 'stop' command
  whaler -v up           Execute with verbose/debug logging

The whalefile.py file in the current directory will be executed with the
specified command and services available via sys.argv.
        """,
    )

    parser.add_argument(
        "command",
        choices=["up", "build", "down", "stop"],
        help="Command to execute (up, build, down, or stop)",
    )

    parser.add_argument(
        "services",
        nargs="*",
        default=[],
        help="Optional service names to operate on",
    )

    parser.add_argument(
        "-f",
        "--file",
        default="whalefile.py",
        help="Path to whaler file (default: whalefile.py)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose/debug logging",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"whaler {__version__}",
    )

    args = parser.parse_args()

    error_console = Console(stderr=True)

    # Find whalefile.py file
    try:
        if args.file == "whalefile.py":
            whaler_file = find_whaler_file()
        else:
            whaler_file = Path(args.file)
            if not whaler_file.exists():
                error_console.print(f"[red]Error: File not found: {whaler_file}[/red]")
                sys.exit(1)
    except FileNotFoundError as e:
        error_console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    # Execute whalefile.py with command
    try:
        execute_whaler_file(
            whaler_file, args.command, args.services, verbose=args.verbose
        )
        sys.exit(0)
    except KeyboardInterrupt:
        error_console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        error_console.print(f"[red]Error executing whalefile.py: {e}[/red]")
        if args.verbose:
            error_console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()

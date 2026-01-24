"""User interface utilities for interactive input."""

from __future__ import annotations

from typing import cast

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.status import Status


class TUI:
    """Terminal User Interface for whaler CLI.

    Provides colored output, prompts, and interactive input with
    shared console instances across the application.
    """

    def __init__(
        self,
        console: Console | None = None,
        error_console: Console | None = None,
    ) -> None:
        """Initialize TUI with consoles.

        Args:
            console: Rich Console for stdout (created if None)
            error_console: Rich Console for stderr (created if None)
        """
        self._console = console or Console()
        self._error_console = error_console or Console(stderr=True)

    @property
    def console(self) -> Console:
        """Get the stdout console instance.

        Returns:
            Rich Console for stdout
        """
        return self._console

    @property
    def error_console(self) -> Console:
        """Get the stderr console instance.

        Returns:
            Rich Console for stderr
        """
        return self._error_console

    def status(self, message: str, spinner: str = "dots") -> Status:
        """Create a status spinner context manager.

        Args:
            message: Message to display next to spinner
            spinner: Name of spinner animation to use

        Returns:
            Rich Status context manager
        """
        return self._console.status(message, spinner=spinner)

    def input(self, prompt: str = "", default: str | None = None) -> str:
        """Interactive input function with optional default.

        Args:
            prompt: Prompt message to display
            default: Default value if user enters nothing

        Returns:
            User input or default value
        """
        return cast(
            str,
            Prompt.ask(
                prompt,
                default=default,
                show_default=True if default is not None else False,
            ),
        )

    def confirm(self, prompt: str, default: bool = False) -> bool:
        """Ask user for yes/no confirmation.

        Args:
            prompt: Confirmation prompt message
            default: Default value if user presses Enter

        Returns:
            True if user confirms, False otherwise
        """
        return cast(bool, Confirm.ask(prompt, default=default))

    def secret_input(self, prompt: str = "Password") -> str:
        """Get secret input (password) without echoing to screen.

        Args:
            prompt: Prompt message to display

        Returns:
            User's secret input
        """
        return cast(str, Prompt.ask(prompt, password=True))

    def info(self, message: str) -> None:
        """Print info message with color.

        Args:
            message: Message to display
        """
        self._console.print(f"[cyan][>][/cyan] {message}")

    def success(self, message: str) -> None:
        """Print success message with color.

        Args:
            message: Success message to display
        """
        self._console.print(f"\n[green][+][/green] {message}\n")

    def error(self, message: str) -> None:
        """Print error message with color.

        Args:
            message: Error message to display
        """
        self._error_console.print(f"[red][X] {message}[/red]")

    def warning(self, message: str) -> None:
        """Print warning message with color.

        Args:
            message: Warning message to display
        """
        self._console.print(f"[yellow][!][/yellow] {message}")


# Module-level singleton instance
tui = TUI()

__all__ = ["TUI", "tui"]

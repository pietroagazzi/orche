"""Custom exceptions for the Orche library."""


class OrcheError(Exception):
    """Base exception for all Orche errors."""

    pass


class DockerComposeError(OrcheError):
    """Raised when a docker-compose command fails."""

    pass


class CommandError(OrcheError):
    """Raised when a command is not found in the registry."""

    pass


class HookError(OrcheError):
    """Raised when a command hook fails during execution."""

    def __init__(self, hook_type: str, command: str, cause: Exception) -> None:
        self.hook_type = hook_type
        self.command = command
        super().__init__(f"{hook_type}-hook for '{command}' failed: {cause}")


class OrchefileError(OrcheError):
    """Raised when the orchefile cannot be loaded or is invalid."""

    pass


class ConfigError(OrcheError):
    """Raised for invalid configuration (e.g. missing compose files, bad params)."""

    pass

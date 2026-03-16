"""Custom exceptions for the Orche library."""


class OrcheError(Exception):
    """Base exception for all Orche errors."""

    pass


class DockerComposeError(OrcheError):
    """Raised when docker-compose command fails."""

    pass

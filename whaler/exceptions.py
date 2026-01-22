"""Custom exceptions for the Whaler library."""


class WhalerError(Exception):
    """Base exception for all Whaler errors."""

    pass


class DockerComposeError(WhalerError):
    """Raised when docker-compose command fails."""

    pass

"""Tests for the exception hierarchy."""

from orche.exceptions import (
    CommandError,
    ConfigError,
    DockerComposeError,
    HookError,
    OrcheError,
    OrchefileError,
)


class TestExceptionHierarchy:
    def test_orche_error_is_exception(self) -> None:
        assert issubclass(OrcheError, Exception)

    def test_docker_compose_error_inherits_orche_error(self) -> None:
        assert issubclass(DockerComposeError, OrcheError)

    def test_command_error_inherits_orche_error(self) -> None:
        assert issubclass(CommandError, OrcheError)

    def test_hook_error_inherits_orche_error(self) -> None:
        assert issubclass(HookError, OrcheError)

    def test_orchefile_error_inherits_orche_error(self) -> None:
        assert issubclass(OrchefileError, OrcheError)

    def test_config_error_inherits_orche_error(self) -> None:
        assert issubclass(ConfigError, OrcheError)


class TestHookError:
    def test_stores_hook_type_and_command(self) -> None:
        err = HookError("before", "up", ValueError("boom"))
        assert err.hook_type == "before"
        assert err.command == "up"

    def test_message_format(self) -> None:
        cause = RuntimeError("connection lost")
        err = HookError("after", "deploy", cause)
        assert "after-hook" in str(err)
        assert "deploy" in str(err)
        assert "connection lost" in str(err)

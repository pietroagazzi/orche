"""Tests for the Stack class."""

from __future__ import annotations

from typing import Any

import pytest

from orche.exceptions import CommandError, ConfigError, HookError
from orche.stack import Stack


class TestStackInit:
    def test_default_compose_file(self, tmp_path: Any, mocker: Any) -> None:
        compose = tmp_path / "docker-compose.yml"
        compose.write_text("services: {}")
        mocker.patch("orche.stack.DockerComposeWrapper")
        mocker.patch("shutil.which", return_value="/usr/bin/docker")

        s = Stack(path=tmp_path)
        assert len(s.compose_files) == 1
        assert s.compose_files[0].name == "docker-compose.yml"

    def test_custom_compose_files(self, tmp_path: Any, mocker: Any) -> None:
        f1 = tmp_path / "a.yml"
        f2 = tmp_path / "b.yml"
        f1.write_text("services: {}")
        f2.write_text("services: {}")
        mocker.patch("orche.stack.DockerComposeWrapper")
        mocker.patch("shutil.which", return_value="/usr/bin/docker")

        s = Stack(path=tmp_path, compose_files=["a.yml", "b.yml"])
        assert len(s.compose_files) == 2

    def test_empty_compose_files_raises_config_error(
        self, tmp_path: Any, mocker: Any
    ) -> None:
        mocker.patch("orche.stack.DockerComposeWrapper")
        with pytest.raises(ConfigError, match="cannot be an empty list"):
            Stack(path=tmp_path, compose_files=[])

    def test_missing_compose_file_raises_config_error(
        self, tmp_path: Any, mocker: Any
    ) -> None:
        mocker.patch("orche.stack.DockerComposeWrapper")
        with pytest.raises(ConfigError, match="not found"):
            Stack(path=tmp_path, compose_files=["nonexistent.yml"])

    def test_project_path_is_resolved(self, make_stack: Any) -> None:
        s = make_stack()
        assert s.project_path.is_absolute()


class TestStackOn:
    def test_no_active_services_returns_true(self, stack: Stack) -> None:
        assert stack.on("anything") is True

    def test_matching_service_returns_true(self, stack: Stack) -> None:
        stack._active_services = ["web", "db"]
        assert stack.on("web") is True

    def test_non_matching_service_returns_false(self, stack: Stack) -> None:
        stack._active_services = ["web"]
        assert stack.on("db") is False

    def test_string_input_accepted(self, stack: Stack) -> None:
        stack._active_services = ["web"]
        assert stack.on("web") is True

    def test_or_logic_any_match(self, stack: Stack) -> None:
        stack._active_services = ["db"]
        assert stack.on(["web", "db"]) is True

    def test_or_logic_no_match(self, stack: Stack) -> None:
        stack._active_services = ["cache"]
        assert stack.on(["web", "db"]) is False


class TestStackDelegation:
    def test_build_delegates_to_docker(self, stack: Stack) -> None:
        stack.build()
        stack._docker.build.assert_called_once()  # type: ignore[attr-defined]

    def test_build_returns_self(self, stack: Stack) -> None:
        assert stack.build() is stack

    def test_up_delegates_to_docker(self, stack: Stack) -> None:
        stack.up()
        stack._docker.up.assert_called_once()  # type: ignore[attr-defined]

    def test_up_returns_self(self, stack: Stack) -> None:
        assert stack.up() is stack

    def test_down_delegates_to_docker(self, stack: Stack) -> None:
        stack.down()
        stack._docker.down.assert_called_once()  # type: ignore[attr-defined]

    def test_down_returns_self(self, stack: Stack) -> None:
        assert stack.down() is stack

    def test_stop_delegates_to_docker(self, stack: Stack) -> None:
        stack.stop()
        stack._docker.stop.assert_called_once()  # type: ignore[attr-defined]

    def test_stop_returns_self(self, stack: Stack) -> None:
        assert stack.stop() is stack

    def test_build_passes_active_services(self, stack: Stack) -> None:
        stack._active_services = ["web"]
        stack.build()
        stack._docker.build.assert_called_once_with(services=["web"])  # type: ignore[attr-defined]

    def test_client_returns_docker_wrapper(self, stack: Stack) -> None:
        assert stack.client() is stack._docker


class TestStackRun:
    def test_unknown_command_raises_command_error(self, stack: Stack) -> None:
        with pytest.raises(CommandError, match="Unknown command"):
            stack.run("nonexistent")

    def test_unknown_command_shows_available(self, stack: Stack) -> None:
        @stack.commands.up
        def handler() -> None:
            pass

        with pytest.raises(CommandError, match="Available: up"):
            stack.run("missing")

    def test_executes_registered_handler(self, stack: Stack) -> None:
        called = False

        @stack.commands.register("deploy")
        def handler() -> None:
            nonlocal called
            called = True

        stack.run("deploy")
        assert called

    def test_sets_active_services(self, stack: Stack) -> None:
        @stack.commands.up
        def handler() -> None:
            pass

        stack.run("up", services=["web", "db"])
        assert stack._active_services == ["web", "db"]

    def test_before_hooks_execute_in_order(self, stack: Stack) -> None:
        order: list[str] = []

        handle = stack.commands.register("up")

        @handle.before
        def first() -> None:
            order.append("first")

        @handle.before
        def second() -> None:
            order.append("second")

        @handle
        def handler() -> None:
            order.append("handler")

        stack.run("up")
        assert order == ["first", "second", "handler"]

    def test_after_hooks_execute_in_order(self, stack: Stack) -> None:
        order: list[str] = []

        handle = stack.commands.register("up")

        @handle
        def handler() -> None:
            order.append("handler")

        @handle.after
        def first() -> None:
            order.append("after1")

        @handle.after
        def second() -> None:
            order.append("after2")

        stack.run("up")
        assert order == ["handler", "after1", "after2"]

    def test_before_hook_failure_skips_handler_and_after(self, stack: Stack) -> None:
        order: list[str] = []

        handle = stack.commands.register("up")

        @handle.before
        def bad_hook() -> None:
            raise RuntimeError("fail")

        @handle
        def handler() -> None:
            order.append("handler")

        @handle.after
        def after() -> None:
            order.append("after")

        with pytest.raises(HookError, match="before-hook"):
            stack.run("up")

        assert order == []  # neither handler nor after ran

    def test_handler_failure_raises_command_error(self, stack: Stack) -> None:
        @stack.commands.register("deploy")
        def handler() -> None:
            raise RuntimeError("boom")

        with pytest.raises(CommandError, match="failed"):
            stack.run("deploy")

    def test_handler_failure_skips_after_hooks(self, stack: Stack) -> None:
        order: list[str] = []
        handle = stack.commands.register("up")

        @handle
        def handler() -> None:
            raise RuntimeError("boom")

        @handle.after
        def after() -> None:
            order.append("after")

        with pytest.raises(CommandError):
            stack.run("up")

        assert order == []

    def test_after_hook_failure_raises_hook_error(self, stack: Stack) -> None:
        handle = stack.commands.register("up")

        @handle
        def handler() -> None:
            pass

        @handle.after
        def bad_after() -> None:
            raise RuntimeError("cleanup failed")

        with pytest.raises(HookError, match="after-hook"):
            stack.run("up")

    def test_hook_error_preserves_cause(self, stack: Stack) -> None:
        cause = ValueError("original")
        handle = stack.commands.register("up")

        @handle.before
        def bad_hook() -> None:
            raise cause

        @handle
        def handler() -> None:
            pass

        with pytest.raises(HookError) as exc_info:
            stack.run("up")

        assert exc_info.value.__cause__ is cause

    def test_full_lifecycle_all_succeed(self, stack: Stack) -> None:
        order: list[str] = []
        handle = stack.commands.register("deploy")

        @handle.before
        def before() -> None:
            order.append("before")

        @handle
        def handler() -> None:
            order.append("handler")

        @handle.after
        def after() -> None:
            order.append("after")

        stack.run("deploy")
        assert order == ["before", "handler", "after"]

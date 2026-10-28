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

    def test_down_rejects_active_services(self, stack: Stack) -> None:
        stack._active_services = ["web"]
        with pytest.raises(ConfigError, match="Use 'rm'"):
            stack.down()
        stack._docker.down.assert_not_called()  # type: ignore[attr-defined]

    def test_rm_passes_explicit_services(self, stack: Stack) -> None:
        stack.rm(services=["web"], volumes=True)
        stack._docker.rm.assert_called_once_with(  # type: ignore[attr-defined]
            services=["web"], volumes=True
        )

    def test_rm_uses_active_services(self, stack: Stack) -> None:
        stack._active_services = ["db"]
        assert stack.rm() is stack
        stack._docker.rm.assert_called_once_with(  # type: ignore[attr-defined]
            services=["db"], volumes=False
        )

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

    def test_sets_active_services_during_run(self, stack: Stack) -> None:
        seen: list[str] = []

        @stack.commands.up
        def handler() -> None:
            seen.extend(stack._active_services)

        stack.run("up", services=["web", "db"])
        assert seen == ["web", "db"]

    def test_active_services_cleared_after_run(self, stack: Stack) -> None:
        @stack.commands.up
        def handler() -> None:
            pass

        stack.run("up", services=["web"])
        assert stack._active_services == []

    def test_active_services_cleared_after_failure(self, stack: Stack) -> None:
        @stack.commands.up
        def handler() -> None:
            raise RuntimeError("boom")

        with pytest.raises(CommandError):
            stack.run("up", services=["web"])
        assert stack._active_services == []

    def test_nested_run_restores_outer_services(self, stack: Stack) -> None:
        seen: list[list[str]] = []

        @stack.commands.build
        def build() -> None:
            seen.append(list(stack._active_services))

        @stack.commands.up
        def up() -> None:
            stack.run("build", services=["db"])
            seen.append(list(stack._active_services))

        stack.run("up", services=["web"])
        assert seen == [["db"], ["web"]]

    def test_concurrent_runs_are_isolated(self, stack: Stack) -> None:
        import threading

        barrier = threading.Barrier(2)
        seen: dict[str, list[str]] = {}

        @stack.commands.up
        def up() -> None:
            barrier.wait(timeout=5)
            seen[threading.current_thread().name] = list(stack._active_services)

        threads = [
            threading.Thread(target=stack.run, args=("up", [svc]), name=svc)
            for svc in ("web", "db")
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert seen == {"web": ["web"], "db": ["db"]}

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


class TestServicesSummary:
    @staticmethod
    def _container(service: str, ports: dict[str, Any]) -> Any:
        from unittest.mock import MagicMock

        c = MagicMock()
        c.name = service
        c.config.labels = {"com.docker.compose.service": service}
        c.network_settings.ports = ports
        return c

    def _urls(self, stack: Stack, mocker: Any) -> list[str]:
        mocker.patch.object(
            stack._docker,
            "ps",
            return_value=[
                self._container("web", {"80/tcp": [{"HostPort": "8080"}]}),
                self._container("tls", {"443/tcp": [{"HostPort": "8443"}]}),
            ],
        )
        printed: list[Any] = []
        mocker.patch(
            "orche.stack.get_console"
        ).return_value.print.side_effect = printed.append
        stack.print_services_summary()
        table = printed[0].renderable
        return [str(cell) for cell in table.columns[2]._cells]

    def test_explicit_host_is_used_without_detection(
        self, make_stack: Any, mocker: Any
    ) -> None:
        detect = mocker.patch("orche.stack._get_local_ip")
        stack = make_stack(host="myhost.local")

        assert self._urls(stack, mocker) == [
            "http://myhost.local:8080",
            "https://myhost.local:8443",
        ]
        detect.assert_not_called()

    def test_detected_ip_is_used_when_host_omitted(
        self, stack: Stack, mocker: Any
    ) -> None:
        mocker.patch("orche.stack._get_local_ip", return_value="10.0.0.5")

        assert self._urls(stack, mocker)[0] == "http://10.0.0.5:8080"


class TestGetLocalIp:
    def test_falls_back_to_loopback_and_warns(self, mocker: Any) -> None:
        from orche.stack import _get_local_ip

        sock = mocker.patch("orche.stack.socket.socket").return_value
        sock.connect.side_effect = OSError("network unreachable")
        warn = mocker.patch("orche.stack.get_logger").return_value.warning

        assert _get_local_ip() == "127.0.0.1"
        warn.assert_called_once()
        sock.close.assert_called_once()


class TestCommandOptions:
    def test_parse_args_splits_services_and_options(self, stack: Stack) -> None:
        @stack.commands.register("deploy")
        def deploy(env: str = "dev", force: bool = False, replicas: int = 1) -> None:
            pass

        services, options = stack.parse_args(
            "deploy", ["web", "--env", "prod", "--force", "--replicas=3", "db"]
        )
        assert services == ["web", "db"]
        assert options == {"env": "prod", "force": True, "replicas": 3}

    def test_parse_args_fills_defaults(self, stack: Stack) -> None:
        @stack.commands.register("deploy")
        def deploy(env: str = "dev") -> None:
            pass

        assert stack.parse_args("deploy", []) == ([], {"env": "dev"})

    def test_bool_negation_and_underscore_flag(self, stack: Stack) -> None:
        @stack.commands.register("deploy")
        def deploy(dry_run: bool = True) -> None:
            pass

        _, options = stack.parse_args("deploy", ["--no-dry-run"])
        assert options == {"dry_run": False}
        _, options = stack.parse_args("deploy", ["--dry-run=false"])
        assert options == {"dry_run": False}

    def test_unannotated_parameter_infers_type_from_default(self, stack: Stack) -> None:
        @stack.commands.register("deploy")
        def deploy(retries=2) -> None:  # type: ignore[no-untyped-def]
            pass

        _, options = stack.parse_args("deploy", ["--retries", "5"])
        assert options == {"retries": 5}

    def test_optional_annotation_is_unwrapped(self, stack: Stack) -> None:
        @stack.commands.register("deploy")
        def deploy(tag: str | None = None) -> None:
            pass

        assert stack.parse_args("deploy", ["--tag", "v1"])[1] == {"tag": "v1"}
        assert stack.parse_args("deploy", [])[1] == {"tag": None}

    def test_list_option_collects_repeated_flags(self, stack: Stack) -> None:
        @stack.commands.register("deploy")
        def deploy(tag: list[str] | None = None, port: list[int] | None = None) -> None:
            pass

        services, options = stack.parse_args(
            "deploy", ["web", "--tag", "a", "--tag=b", "--port", "80", "--port", "81"]
        )
        assert services == ["web"]
        assert options == {"tag": ["a", "b"], "port": [80, 81]}
        assert stack.parse_args("deploy", [])[1] == {"tag": None, "port": None}

    def test_list_option_rejects_invalid_item(self, stack: Stack) -> None:
        @stack.commands.register("deploy")
        def deploy(port: list[int]) -> None:
            pass

        with pytest.raises(CommandError, match="Invalid value for --port"):
            stack.parse_args("deploy", ["--port", "80", "--port", "x"])

    def test_required_list_option(self, stack: Stack) -> None:
        @stack.commands.register("deploy")
        def deploy(tag: list[str]) -> None:
            pass

        with pytest.raises(CommandError, match="Missing required option --tag"):
            stack.parse_args("deploy", [])

    def test_list_default_is_copied(self, stack: Stack) -> None:
        @stack.commands.register("deploy")
        def deploy(tag: list[str] = ["latest"]) -> None:  # noqa: B006
            pass

        _, first = stack.parse_args("deploy", [])
        first["tag"].append("x")
        assert stack.parse_args("deploy", [])[1] == {"tag": ["latest"]}

    def test_unannotated_list_default_is_a_list_of_str(self, stack: Stack) -> None:
        @stack.commands.register("deploy")
        def deploy(tag=["latest"]) -> None:  # type: ignore[no-untyped-def]  # noqa: B006
            pass

        assert stack.parse_args("deploy", ["--tag", "a", "--tag", "b"])[1] == {
            "tag": ["a", "b"]
        }

    def test_list_of_bool_is_rejected(self, stack: Stack) -> None:
        with pytest.raises(ConfigError, match="unsupported type"):

            @stack.commands.register("deploy")
            def deploy(flag: list[bool]) -> None:
                pass

    def test_negative_number_is_a_value(self, stack: Stack) -> None:
        @stack.commands.register("deploy")
        def deploy(offset: int = 0) -> None:
            pass

        assert stack.parse_args("deploy", ["--offset", "-1"])[1] == {"offset": -1}

    def test_double_dash_ends_options(self, stack: Stack) -> None:
        @stack.commands.register("deploy")
        def deploy() -> None:
            pass

        assert stack.parse_args("deploy", ["--", "--odd"]) == (["--odd"], {})

    def test_unknown_option_lists_available(self, stack: Stack) -> None:
        @stack.commands.register("deploy")
        def deploy(env: str = "dev") -> None:
            pass

        with pytest.raises(CommandError, match=r"Unknown option '--nope'.*--env"):
            stack.parse_args("deploy", ["--nope"])

    def test_option_on_command_without_options(self, stack: Stack) -> None:
        @stack.commands.up
        def up() -> None:
            pass

        with pytest.raises(CommandError, match="takes no options"):
            stack.parse_args("up", ["--env", "prod"])

    def test_short_option_is_rejected(self, stack: Stack) -> None:
        @stack.commands.up
        def up() -> None:
            pass

        with pytest.raises(CommandError, match="Unknown option '-x'"):
            stack.parse_args("up", ["-x"])

    def test_missing_value(self, stack: Stack) -> None:
        @stack.commands.register("deploy")
        def deploy(env: str = "dev") -> None:
            pass

        with pytest.raises(CommandError, match="requires a value"):
            stack.parse_args("deploy", ["--env"])

    @pytest.mark.parametrize("next_token", ["--dry-run", "--unknown", "-x", "--"])
    def test_value_is_not_swallowed_from_next_option(
        self, stack: Stack, next_token: str
    ) -> None:
        @stack.commands.register("deploy")
        def deploy(env: str = "dev", dry_run: bool = False) -> None:
            pass

        with pytest.raises(CommandError, match="requires a value"):
            stack.parse_args("deploy", ["--env", next_token])

    def test_invalid_value(self, stack: Stack) -> None:
        @stack.commands.register("deploy")
        def deploy(replicas: int = 1) -> None:
            pass

        with pytest.raises(CommandError, match="expected int"):
            stack.parse_args("deploy", ["--replicas", "many"])

    def test_missing_required_option(self, stack: Stack) -> None:
        @stack.commands.register("deploy")
        def deploy(env: str) -> None:
            pass

        with pytest.raises(CommandError, match="Missing required option --env"):
            stack.parse_args("deploy", [])

    def test_parse_args_unknown_command(self, stack: Stack) -> None:
        with pytest.raises(CommandError, match="Unknown command"):
            stack.parse_args("missing", [])

    def test_unsupported_type_fails_at_registration(self, stack: Stack) -> None:
        with pytest.raises(ConfigError, match="unsupported type"):

            @stack.commands.register("deploy")
            def deploy(tags: dict[str, str]) -> None:
                pass

    def test_reserved_flag_fails_at_registration(self, stack: Stack) -> None:
        with pytest.raises(ConfigError, match="reserved"):

            @stack.commands.register("deploy")
            def deploy(debug: bool = False) -> None:
                pass

    def test_handler_receives_options(self, stack: Stack) -> None:
        received: dict[str, object] = {}

        @stack.commands.register("deploy")
        def deploy(env: str = "dev", force: bool = False) -> None:
            received.update(env=env, force=force)

        stack.run("deploy", options={"env": "prod"})
        assert received == {"env": "prod", "force": False}

    def test_run_rejects_unknown_option(self, stack: Stack) -> None:
        @stack.commands.register("deploy")
        def deploy() -> None:
            pass

        with pytest.raises(CommandError, match="Unknown option"):
            stack.run("deploy", options={"env": "prod"})

    def test_hooks_receive_only_declared_options(self, stack: Stack) -> None:
        calls: list[tuple[str, object]] = []

        @stack.commands.register("deploy")
        def deploy(env: str = "dev", force: bool = False) -> None:
            pass

        @stack.commands.register("deploy").before
        def check(env: str) -> None:
            calls.append(("before", env))

        @stack.commands.register("deploy").after
        def done() -> None:
            calls.append(("after", None))

        stack.run("deploy", options={"env": "prod"})
        assert calls == [("before", "prod"), ("after", None)]

    def test_hook_with_var_keyword_receives_all_options(self, stack: Stack) -> None:
        seen: dict[str, object] = {}

        @stack.commands.register("deploy")
        def deploy(env: str = "dev") -> None:
            pass

        @stack.commands.register("deploy").before
        def check(**kwargs: object) -> None:
            seen.update(kwargs)

        stack.run("deploy", options={"env": "prod"})
        assert seen == {"env": "prod"}

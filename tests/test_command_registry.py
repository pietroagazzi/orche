"""Tests for CommandRegistry and CommandHandle."""

from collections.abc import Callable

from orche.stack import CommandHandle, CommandRegistry


def _noop() -> None:
    pass


class TestCommandRegistry:
    def test_register_returns_command_handle(self) -> None:
        reg: CommandRegistry[Callable[[], None]] = CommandRegistry()
        handle = reg.register("deploy")
        assert isinstance(handle, CommandHandle)

    def test_get_unregistered_returns_none(self) -> None:
        reg: CommandRegistry[Callable[[], None]] = CommandRegistry()
        assert reg.get("missing") is None

    def test_available_commands_empty_initially(self) -> None:
        reg: CommandRegistry[Callable[[], None]] = CommandRegistry()
        assert reg.available_commands() == []

    def test_available_commands_lists_registered(self) -> None:
        reg: CommandRegistry[Callable[[], None]] = CommandRegistry()
        reg.register("up")(_noop)
        reg.register("down")(_noop)
        assert sorted(reg.available_commands()) == ["down", "up"]

    def test_get_before_hooks_empty_by_default(self) -> None:
        reg: CommandRegistry[Callable[[], None]] = CommandRegistry()
        assert reg.get_before_hooks("up") == []

    def test_get_after_hooks_empty_by_default(self) -> None:
        reg: CommandRegistry[Callable[[], None]] = CommandRegistry()
        assert reg.get_after_hooks("up") == []


class TestCommandHandle:
    def test_call_registers_handler(self) -> None:
        reg: CommandRegistry[Callable[[], None]] = CommandRegistry()
        handle = reg.register("up")
        handle(_noop)
        assert reg.get("up") is _noop

    def test_call_returns_original_function(self) -> None:
        reg: CommandRegistry[Callable[[], None]] = CommandRegistry()
        result = reg.register("up")(_noop)
        assert result is _noop

    def test_before_registers_hook(self) -> None:
        reg: CommandRegistry[Callable[[], None]] = CommandRegistry()
        handle = reg.register("up")
        handle.before(_noop)
        assert _noop in reg.get_before_hooks("up")

    def test_after_registers_hook(self) -> None:
        reg: CommandRegistry[Callable[[], None]] = CommandRegistry()
        handle = reg.register("up")
        handle.after(_noop)
        assert _noop in reg.get_after_hooks("up")

    def test_multiple_before_hooks_preserved_in_order(self) -> None:
        reg: CommandRegistry[Callable[[], None]] = CommandRegistry()
        handle = reg.register("up")
        calls: list[int] = []

        def hook_a() -> None:
            calls.append(1)

        def hook_b() -> None:
            calls.append(2)

        handle.before(hook_a)
        handle.before(hook_b)
        hooks = reg.get_before_hooks("up")
        assert hooks == [hook_a, hook_b]

    def test_multiple_after_hooks_preserved_in_order(self) -> None:
        reg: CommandRegistry[Callable[[], None]] = CommandRegistry()
        handle = reg.register("up")
        calls: list[int] = []

        def hook_a() -> None:
            calls.append(1)

        def hook_b() -> None:
            calls.append(2)

        handle.after(hook_a)
        handle.after(hook_b)
        hooks = reg.get_after_hooks("up")
        assert hooks == [hook_a, hook_b]


class TestPropertyShortcuts:
    def test_up_registers_as_up(self) -> None:
        reg: CommandRegistry[Callable[[], None]] = CommandRegistry()
        reg.up(_noop)
        assert reg.get("up") is _noop

    def test_down_registers_as_down(self) -> None:
        reg: CommandRegistry[Callable[[], None]] = CommandRegistry()
        reg.down(_noop)
        assert reg.get("down") is _noop

    def test_build_registers_as_build(self) -> None:
        reg: CommandRegistry[Callable[[], None]] = CommandRegistry()
        reg.build(_noop)
        assert reg.get("build") is _noop

    def test_stop_registers_as_stop(self) -> None:
        reg: CommandRegistry[Callable[[], None]] = CommandRegistry()
        reg.stop(_noop)
        assert reg.get("stop") is _noop

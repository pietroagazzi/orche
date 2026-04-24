"""Tests for the CLI module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from orche.cli import _parse_chained, find_or_validate_orchefile, main
from orche.exceptions import CommandError, HookError, OrcheError, OrchefileError


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


class TestMainCommand:
    def test_version_flag(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "orche" in result.output

    def test_orchefile_not_found_exits_1(self, runner: CliRunner, mocker: Any) -> None:
        mocker.patch(
            "orche.cli.find_or_validate_orchefile",
            side_effect=OrchefileError("not found"),
        )
        result = runner.invoke(main, ["up"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_command_error_exits_1(self, runner: CliRunner, mocker: Any) -> None:
        mock_stack = mocker.MagicMock()
        mock_stack.run.side_effect = CommandError("unknown command 'foo'")
        mocker.patch("orche.cli.find_or_validate_orchefile")
        mocker.patch("orche.cli.import_orchefile", return_value=mock_stack)

        result = runner.invoke(main, ["foo"])
        assert result.exit_code == 1
        assert "unknown command" in result.output

    def test_orche_error_exits_1(self, runner: CliRunner, mocker: Any) -> None:
        mock_stack = mocker.MagicMock()
        mock_stack.run.side_effect = OrcheError("something broke")
        mocker.patch("orche.cli.find_or_validate_orchefile")
        mocker.patch("orche.cli.import_orchefile", return_value=mock_stack)

        result = runner.invoke(main, ["up"])
        assert result.exit_code == 1
        assert "something broke" in result.output

    def test_hook_error_exits_1(self, runner: CliRunner, mocker: Any) -> None:
        mock_stack = mocker.MagicMock()
        mock_stack.run.side_effect = HookError("before", "up", RuntimeError("x"))
        mocker.patch("orche.cli.find_or_validate_orchefile")
        mocker.patch("orche.cli.import_orchefile", return_value=mock_stack)

        result = runner.invoke(main, ["up"])
        assert result.exit_code == 1
        assert "before-hook" in result.output

    def test_unexpected_error_exits_1(self, runner: CliRunner, mocker: Any) -> None:
        mock_stack = mocker.MagicMock()
        mock_stack.run.side_effect = RuntimeError("unexpected")
        mocker.patch("orche.cli.find_or_validate_orchefile")
        mocker.patch("orche.cli.import_orchefile", return_value=mock_stack)

        result = runner.invoke(main, ["up"])
        assert result.exit_code == 1
        assert "Unexpected error" in result.output

    def test_passes_command_and_services(self, runner: CliRunner, mocker: Any) -> None:
        mock_stack = mocker.MagicMock()
        mocker.patch("orche.cli.find_or_validate_orchefile")
        mocker.patch("orche.cli.import_orchefile", return_value=mock_stack)

        runner.invoke(main, ["up", "web", "db"])
        mock_stack.run.assert_called_once_with(command="up", services=["web", "db"])

    def test_custom_file_option(self, runner: CliRunner, mocker: Any) -> None:
        mock_find = mocker.patch("orche.cli.find_or_validate_orchefile")
        mock_stack = mocker.MagicMock()
        mocker.patch("orche.cli.import_orchefile", return_value=mock_stack)

        runner.invoke(main, ["-f", "custom.py", "up"])
        mock_find.assert_called_once()
        call_arg = mock_find.call_args[0][0]
        assert str(call_arg) == "custom.py"


class TestParseChained:
    def test_single_command_no_services(self) -> None:
        assert _parse_chained("build", ()) == [("build", [])]

    def test_single_command_with_services(self) -> None:
        assert _parse_chained("up", ("web", "db")) == [("up", ["web", "db"])]

    def test_trailing_comma_on_command(self) -> None:
        assert _parse_chained("build,", ("up", "web")) == [
            ("build", []),
            ("up", ["web"]),
        ]

    def test_trailing_comma_on_service(self) -> None:
        assert _parse_chained("up", ("web,", "build")) == [
            ("up", ["web"]),
            ("build", []),
        ]

    def test_standalone_comma_separator(self) -> None:
        assert _parse_chained("build", (",", "up", "web")) == [
            ("build", []),
            ("up", ["web"]),
        ]

    def test_three_chained_commands(self) -> None:
        assert _parse_chained("build,", ("up,", "stop")) == [
            ("build", []),
            ("up", []),
            ("stop", []),
        ]

    def test_services_on_multiple_commands(self) -> None:
        assert _parse_chained("up", ("web", "db,", "build", "api")) == [
            ("up", ["web", "db"]),
            ("build", ["api"]),
        ]


class TestChainedExecution:
    def test_executes_all_commands_in_order(
        self, runner: CliRunner, mocker: Any
    ) -> None:
        mock_stack = mocker.MagicMock()
        mocker.patch("orche.cli.find_or_validate_orchefile")
        mocker.patch("orche.cli.import_orchefile", return_value=mock_stack)

        result = runner.invoke(main, ["build,", "up", "web"])
        assert result.exit_code == 0
        assert mock_stack.run.call_count == 2
        mock_stack.run.assert_any_call(command="build", services=[])
        mock_stack.run.assert_any_call(command="up", services=["web"])

    def test_stops_on_first_failure(self, runner: CliRunner, mocker: Any) -> None:
        mock_stack = mocker.MagicMock()
        mock_stack.run.side_effect = CommandError("build failed")
        mocker.patch("orche.cli.find_or_validate_orchefile")
        mocker.patch("orche.cli.import_orchefile", return_value=mock_stack)

        result = runner.invoke(main, ["build,", "up"])
        assert result.exit_code == 1
        assert mock_stack.run.call_count == 1

    def test_loads_orchefile_once_for_chain(
        self, runner: CliRunner, mocker: Any
    ) -> None:
        mock_import = mocker.patch(
            "orche.cli.import_orchefile", return_value=mocker.MagicMock()
        )
        mocker.patch("orche.cli.find_or_validate_orchefile")

        runner.invoke(main, ["build,", "up,", "stop"])
        assert mock_import.call_count == 1


class TestFindOrValidateOrchefile:
    def test_default_found(self, tmp_path: Path, monkeypatch: Any) -> None:
        orchefile = tmp_path / "orchefile.py"
        orchefile.write_text("# empty")
        monkeypatch.chdir(tmp_path)

        result = find_or_validate_orchefile(Path("orchefile.py"))
        assert result.name == "orchefile.py"
        assert result.is_absolute()

    def test_default_not_found_raises(self, tmp_path: Path, monkeypatch: Any) -> None:
        monkeypatch.chdir(tmp_path)
        with pytest.raises(OrchefileError, match="not found"):
            find_or_validate_orchefile(Path("orchefile.py"))

    def test_custom_path_found(self, tmp_path: Path) -> None:
        custom = tmp_path / "my_stack.py"
        custom.write_text("# empty")

        result = find_or_validate_orchefile(custom)
        assert result == custom.resolve()

    def test_custom_path_not_found_raises(self, tmp_path: Path) -> None:
        with pytest.raises(OrchefileError, match="File not found"):
            find_or_validate_orchefile(tmp_path / "missing.py")

"""Tests for built-in utility functions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from orche.builtin import ensure_directory, git_clone, read_yaml
from orche.exceptions import ConfigError, OrcheError


class TestEnsureDirectory:
    def test_creates_new_directory(self, tmp_path: Path) -> None:
        target = tmp_path / "new_dir"
        result = ensure_directory(target)
        assert result.exists()
        assert result.is_dir()

    def test_existing_directory_no_error(self, tmp_path: Path) -> None:
        result = ensure_directory(tmp_path)
        assert result == tmp_path

    def test_permission_error_raises_orche_error(
        self, tmp_path: Path, mocker: Any
    ) -> None:
        mocker.patch.object(Path, "exists", return_value=False)
        mocker.patch.object(Path, "mkdir", side_effect=OSError("Permission denied"))
        with pytest.raises(OrcheError, match="Failed to create directory"):
            ensure_directory(tmp_path / "forbidden")


class TestGitClone:
    def test_calls_repo_clone_from(self, tmp_path: Path, mocker: Any) -> None:
        mock_clone = mocker.patch("orche.builtin.git.Repo.clone_from")
        dest = tmp_path / "repo"

        git_clone("https://example.com/repo.git", dest)
        mock_clone.assert_called_once_with("https://example.com/repo.git", dest)

    def test_with_branch(self, tmp_path: Path, mocker: Any) -> None:
        mock_clone = mocker.patch("orche.builtin.git.Repo.clone_from")
        dest = tmp_path / "repo"

        git_clone("https://example.com/repo.git", dest, branch="main")
        mock_clone.assert_called_once_with(
            "https://example.com/repo.git", dest, branch="main"
        )

    def test_existing_non_empty_dir_skips(self, tmp_path: Path, mocker: Any) -> None:
        mock_clone = mocker.patch("orche.builtin.git.Repo.clone_from")
        (tmp_path / "file.txt").write_text("content")

        git_clone("https://example.com/repo.git", tmp_path)
        mock_clone.assert_not_called()

    def test_failure_raises_orche_error(self, tmp_path: Path, mocker: Any) -> None:
        import git

        mocker.patch(
            "orche.builtin.git.Repo.clone_from",
            side_effect=git.GitCommandError("clone", "failed"),
        )
        dest = tmp_path / "repo"
        with pytest.raises(OrcheError, match="Failed to clone"):
            git_clone("https://example.com/repo.git", dest)


class TestReadYaml:
    def test_valid_file(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "config.yml"
        yaml_file.write_text("key: value\nlist:\n  - a\n  - b\n")

        result = read_yaml(yaml_file)
        assert result == {"key": "value", "list": ["a", "b"]}

    def test_nonexistent_file_raises_config_error(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigError, match="YAML file not found"):
            read_yaml(tmp_path / "missing.yml")

    def test_invalid_yaml_raises_orche_error(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.yml"
        bad.write_text("key: [invalid\n")

        with pytest.raises(OrcheError, match="Error parsing YAML"):
            read_yaml(bad)

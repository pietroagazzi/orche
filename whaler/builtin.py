"""Built-in utility functions for stack operations."""

from pathlib import Path
from typing import Any

import git
import yaml

from .tui import tui


def ensure_directory(path: str | Path) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to the directory

    Returns:
        The Path object of the directory
    """
    p = Path(path)
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)
        tui.info(f"Created directory: {p}")
    return p


def git_clone(repo_url: str, dest: str | Path, branch: str | None = None) -> None:
    """Clone a git repository.

    Args:
        repo_url: URL of the repository
        dest: Destination path
        branch: Optional specific branch/tag to checkout
    """
    dest_path = Path(dest)
    if dest_path.exists() and any(dest_path.iterdir()):
        tui.warning(
            f"Destination {dest} already exists and is not empty. Skipping clone."
        )
        return

    tui.info(f"Cloning {repo_url} into {dest}...")
    try:
        if branch:
            git.Repo.clone_from(repo_url, dest_path, branch=branch)
        else:
            git.Repo.clone_from(repo_url, dest_path)
        tui.success(f"Repository cloned to {dest}")
    except git.exc.GitCommandError as e:
        tui.error(f"Failed to clone repository: {e.stderr}")
        raise


def read_yaml(path: str | Path) -> Any:
    """Read and parse a YAML file.

    Args:
        path: Path to the YAML file

    Returns:
        Parsed YAML content (usually dict or list)

    Raises:
        FileNotFoundError: If file does not exist
        yaml.YAMLError: If file is not valid YAML
    """
    p = Path(path)
    if not p.exists():
        tui.error(f"YAML file not found: {p}")
        raise FileNotFoundError(f"File not found: {p}")

    try:
        with open(p, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        tui.error(f"Error parsing YAML file {p}: {e}")
        raise

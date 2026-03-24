"""Built-in utility functions for stack operations."""

from pathlib import Path
from typing import Any

import git
import yaml

from .exceptions import ConfigError, OrcheError
from .logger import get_logger

logger = get_logger()


def ensure_directory(path: str | Path) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to the directory

    Returns:
        The Path object of the directory

    Raises:
        OrcheError: If directory creation fails
    """
    p = Path(path)
    try:
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {p}")
        return p
    except OSError as e:
        raise OrcheError(f"Failed to create directory '{p}': {e}") from e


def git_clone(repo_url: str, dest: str | Path, branch: str | None = None) -> None:
    """Clone a git repository.

    Args:
        repo_url: URL of the repository
        dest: Destination path
        branch: Optional specific branch/tag to checkout

    Raises:
        OrcheError: If cloning fails
    """
    dest_path = Path(dest)
    if dest_path.exists() and any(dest_path.iterdir()):
        logger.info(
            f"Destination {dest} already exists and is not empty. Skipping clone."
        )
        return

    logger.info(f"Cloning {repo_url} into {dest}...")
    try:
        if branch:
            git.Repo.clone_from(repo_url, dest_path, branch=branch)
        else:
            git.Repo.clone_from(repo_url, dest_path)
        logger.info(f"Repository cloned to {dest}")
    except git.GitCommandError as e:
        raise OrcheError(f"Failed to clone repository '{repo_url}': {e.stderr}") from e


def read_yaml(path: str | Path) -> Any:
    """Read and parse a YAML file.

    Args:
        path: Path to the YAML file

    Returns:
        Parsed YAML content (usually dict or list)

    Raises:
        ConfigError: If file does not exist or is not valid YAML
    """
    p = Path(path)
    if not p.exists():
        raise ConfigError(f"YAML file not found: {p}")

    try:
        with open(p, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise OrcheError(f"Error parsing YAML file '{p}': {e}") from e

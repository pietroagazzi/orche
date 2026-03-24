# Orche

[![CI](https://github.com/pietroagazzi/orche/actions/workflows/ci.yml/badge.svg)](https://github.com/pietroagazzi/orche/actions/workflows/ci.yml)

A simple, lightweight Python orchestrator for Docker Compose stacks.

Define your stack logic in an `orchefile.py`, register commands with decorators, and run everything through the `orche` CLI.

## Installation

```bash
pip install orche
```

## Quick Start

Create an `orchefile.py` in your project root:

```python
from orche import Stack

stack = Stack(
    name="myapp",
    compose_files=["docker-compose.yml"],
)

@stack.commands.up
def up():
    stack.build().up()

@stack.commands.down
def down():
    stack.down(volumes=True)
```

Then run:

```bash
orche up
orche down
```

## Features

- **Command registry** — register built-in (`up`, `down`, `build`, `stop`) and custom commands with decorators
- **Before / after hooks** — run setup, validation, or cleanup around any command
- **Conditional service logic** — `stack.on("service")` to branch based on CLI-targeted services
- **Multiple compose files** — merge compose files in order, with override support
- **Built-in utilities** — `git_clone`, `ensure_directory`, `read_yaml` helpers
- **Method chaining** — `stack.build().up(wait=True)`

## Documentation

Full documentation is available [here](https://pietroagazzi.github.io/orche/):

- [Installation](docs/installation.md)
- [Quick Start](docs/quickstart.md)
- [CLI Reference](docs/cli-reference.md)
- **Guides:** [Hooks](docs/guides/hooks.md) · [Services](docs/guides/services.md)
- **API:** [Stack](docs/api/stack.md) · [Command Registry](docs/api/command-registry.md) · [Built-in Utilities](docs/api/builtin.md) · [Exceptions](docs/api/exceptions.md)

## Requirements

- Python >= 3.10
- Docker and Docker Compose installed on the system

## Development

```bash
pip install -e ".[dev]"
pytest
mypy orche
ruff check orche
```

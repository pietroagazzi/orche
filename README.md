# Orche

[![CI](https://github.com/pietroagazzi/orche/actions/workflows/ci.yml/badge.svg)](https://github.com/pietroagazzi/orche/actions/workflows/ci.yml)

A simple, lightweight Python orchestrator for Docker Compose stacks.

Define your stack logic in an `orchefile.py`, register commands with decorators, and run everything through the `orche` CLI.

> [!IMPORTANT]
> Orche is a **thin orchestration layer** on top of Docker Compose.
> It does not replace Docker — it coordinates what happens around it.

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

# Chain commands with commas
orche build, up
```

## Documentation

Full documentation is available [here](https://pietroagazzi.github.io/orche/):

- [Installation](https://pietroagazzi.github.io/orche/installation/)
- [Quick Start](https://pietroagazzi.github.io/orche/quickstart/)
- [CLI Reference](https://pietroagazzi.github.io/orche/cli-reference/)
- **Guides:** [Hooks](https://pietroagazzi.github.io/orche/guides/hooks/) · [Services](https://pietroagazzi.github.io/orche/guides/services/)
- **API:** [Stack](https://pietroagazzi.github.io/orche/api/stack/) · [Command Registry](https://pietroagazzi.github.io/orche/api/command-registry/) · [Built-in Utilities](https://pietroagazzi.github.io/orche/api/builtin/) · [Exceptions](https://pietroagazzi.github.io/orche/api/exceptions/)

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

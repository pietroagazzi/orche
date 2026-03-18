# Orche

**A Python orchestrator for Docker Compose stacks.**

[![PyPI](https://img.shields.io/pypi/v/orche)](https://pypi.org/project/orche/)
[![Python](https://img.shields.io/pypi/pyversions/orche)](https://pypi.org/project/orche/)
[![License](https://img.shields.io/github/license/pietroagazzi/orche)](https://github.com/pietroagazzi/orche/blob/main/LICENSE)

Orche lets you define your Docker Compose workflow as Python code — with full
control over service ordering, conditional logic, pre/post hooks, and custom commands.

## Quick Install

```bash
pip install orche
```

## Minimal Example

```python title="orchefile.py"
from orche import Stack

stack = Stack(compose_files=["docker-compose.yml"])

@stack.commands.up
def up() -> None:
    stack.build()
    stack.up()

@stack.commands.down
def down() -> None:
    stack.down()
```

```bash
orche up
orche down
```

## Key Features

- **Imperative orchestration** — plain Python, no YAML DSL
- **Service filtering** — `stack.on("service")` targets specific services
- **Pre/post hooks** — run code before or after any command
- **Custom commands** — extend beyond `up`, `build`, `down`, `stop`
- **Docker Compose integration** — wraps `docker compose` with full flag support

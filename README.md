# Orche

[![CI](https://github.com/pietroagazzi/orche/actions/workflows/ci.yml/badge.svg)](https://github.com/pietroagazzi/orche/actions/workflows/ci.yml)

A simple, lightweight Python orchestrator for Docker Compose stacks.

## Installation

```bash
pip install -e .
```

## CLI Reference

The `orche` command executes your `orchefile.py` file with the specified command and services.

```bash
orche [command] [services...]
```

### Commands

- `orche up [services]` - Start services (executes orchefile.py with 'up' command)
- `orche build [services]` - Build services (executes orchefile.py with 'build' command)
- `orche down [services]` - Stop services (executes orchefile.py with 'down' command)

### Options

- `-f, --file FILE` - Path to orche file (default: orchefile.py)
- `-v, --verbose` - Enable verbose logging
- `--version` - Show version and exit
- `--help` - Show help and exit

### Examples

```bash
# Execute orchefile.py with up command
orche up

# Build specific services
orche build api web

# Start specific services
orche up postgres redis

# Use custom orche file
orche -f custom.py up
```

## Examples

### Basic Usage

```python
from orche import Stack

stack = Stack(compose_files=["docker-compose.yml"])
stack.build().up()
```

### With Project Name

```python
from orche import Stack

stack = Stack(
    compose_files=["docker-compose.yml"],
    name="myapp",
    path="/path/to/project"
)

stack.build().up(wait=True)
```

### Specific Services

```python
from orche import Stack

stack = Stack(compose_files=["docker-compose.yml"])

# Build specific services
stack.build(["api", "web"])

# Start specific services
stack.up(["postgres", "redis"])
```


## Requirements

- Python >= 3.10
- Docker and Docker Compose installed on the system

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Type checking:

```bash
mypy orche
```

Linting:

```bash
ruff check orche
```

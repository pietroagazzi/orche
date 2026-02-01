# Whaler

[![CI](https://github.com/pietroagazzi/whaler/actions/workflows/ci.yml/badge.svg)](https://github.com/pietroagazzi/whaler/actions/workflows/ci.yml)

A simple, lightweight Python orchestrator for Docker Compose stacks.

## Installation

```bash
pip install -e .
```

## CLI Reference

The `whaler` command executes your `whalerfile.py` file with the specified command and services.

```bash
whaler [command] [services...]
```

### Commands

- `whaler up [services]` - Start services (executes whalerfile.py with 'up' command)
- `whaler build [services]` - Build services (executes whalerfile.py with 'build' command)
- `whaler down [services]` - Stop services (executes whalerfile.py with 'down' command)

### Options

- `-f, --file FILE` - Path to whaler file (default: whalerfile.py)
- `-v, --version` - Show version
- `-h, --help` - Show help

### Examples

```bash
# Execute whalerfile.py with up command
whaler up

# Build specific services
whaler build api web

# Start specific services
whaler up postgres redis

# Use custom whaler file
whaler -f custom.py up
```

## Examples

### Basic Usage

```python
from whaler import Stack

stack = Stack("docker-compose.yml")
stack.build().up()
```

### With Project Name

```python
from whaler import Stack

stack = Stack(
    compose_files=["docker-compose.yml"],
    project_name="myapp",
    project_path="/path/to/project"
)

stack.build().up(wait=True)
```

### Specific Services

```python
from whaler import Stack

stack = Stack("docker-compose.yml")

# Build specific services
stack.build(["api", "web"])

# Start specific services
stack.up(["postgres", "redis"])
```


## Requirements

- Python >= 3.14
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
mypy whaler
```

Linting:

```bash
ruff check whaler
```

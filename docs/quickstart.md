# Quickstart

## 1. Create an orchefile

In your project root, create `orchefile.py` next to your `docker-compose.yml`.

Relative `compose_files` are resolved from the stack `path` (project root):

```python title="orchefile.py"
from orche import Stack
from rich import print

# Initialize the stack
stack = Stack(
    compose_files=["docker-compose.yml"],
)


# Register the 'up' command
@stack.commands.up
def up() -> None:
    if stack.on("postgres"):
        print("Postgres is included")

    stack.build().up()


# Register the 'down' command
@stack.commands.down
def down() -> None:
    volumes = input("Remove volumes? [y/N]: ").strip().lower()
    stack.down(volumes=volumes == "y")
    print("Stopped")
```

If your compose files live in another directory, set `path` and keep `compose_files` relative to it:

```python title="orchefile.py"
from orche import Stack

stack = Stack(
    path="/path/to/project",
    compose_files=["docker-compose.yml", "docker-compose.override.yml"],
)
```

## 2. Run commands

```bash
# Start all services
orche up

# Start only the 'api' service
orche up api

# Stop and clean up
orche down
```

## 3. Chain commands

Separate multiple commands with commas to run them sequentially in one call:

```bash
# Build then start
orche build, up

# Build a specific service, then start everything
orche build api, up
```

Execution stops at the first failure, so later commands only run if all
earlier ones succeed.

## 4. Next Steps

- [Service Filtering](guides/services.md) — target specific services
- [Hooks](guides/hooks.md) — run code before/after commands
- [Custom Commands](guides/plugins.md) — add your own commands

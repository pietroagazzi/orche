# Quickstart

## 1. Create an orchefile

In your project root, create `orchefile.py` next to your `docker-compose.yml`:

```python title="orchefile.py"
from orche import Stack
from rich import print

# Initialize the stack
stack = Stack(
    compose_files=["docker-compose.yml"],
    load_env=True,  # loads .env automatically
)


# Register the 'up' command
@stack.commands.up
def up() -> None:
    # Conditional logic per service
    if stack.on("postgres"):
        print("Postgres is included")

    stack.build()
    stack.up()


# Register the 'down' command
@stack.commands.down
def down() -> None:
    volumes = input("Remove volumes? [y/N]: ").strip().lower()
    stack.down(volumes=volumes == "y")
    print("Stopped")
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

## 3. Next Steps

- [Service Filtering](guides/services.md) — target specific services
- [Hooks](guides/hooks.md) — run code before/after commands
- [Custom Commands](guides/plugins.md) — add your own commands

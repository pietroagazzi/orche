# Service Filtering

`stack.on()` lets you run conditional logic based on which services were requested via the CLI.

## Basic Usage

```python
@stack.commands.up
def up() -> None:
    if stack.on("postgres"):
        print("Postgres is active — running migrations")
        run_migrations()

    stack.up()
```

```bash
# Runs migrations
orche up postgres

# Skips migrations
orche up api
```

## OR Logic

Pass a list to check if **any** of the services are active:

```python
if stack.on(["postgres", "mysql"]):
    run_migrations()
```

## All Services Active

When no services are specified on the CLI, `stack.on()` always returns `True` — all services are considered active.

```bash
# stack.on("postgres") → True (no filter applied)
orche up
```

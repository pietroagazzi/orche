# Hooks (Pre/Post)

Hooks let you run code **before** or **after** any command without modifying the command handler itself.

## Before Hook

```python
@stack.commands.up.before
def pre_up() -> None:
    print("Checking prerequisites...")
    check_env_vars()
```

## After Hook

After-hooks always run, even if the main command fails.

```python
@stack.commands.up.after
def post_up() -> None:
    print("Deployment complete — notifying Slack")
    notify_slack()
```

## Full Example

```python
from orche import Stack

stack = Stack(compose_files=["docker-compose.yml"])


@stack.commands.up.before
def pre_up() -> None:
    print("Running pre-flight checks...")


@stack.commands.up
def up() -> None:
    stack.build()
    stack.up()


@stack.commands.up.after
def post_up() -> None:
    print("Services are live.")
```

```bash
orche up
# Running pre-flight checks...
# [build / up output]
# Services are live.
```

## Multiple Hooks

You can register multiple before/after hooks. They run in registration order.

```python
@stack.commands.up.before
def check_docker() -> None: ...

@stack.commands.up.before
def check_env() -> None: ...
```

## Error Handling

- Before-hook exceptions propagate and abort the command.
- After-hook exceptions are logged as warnings and do **not** mask the main result.

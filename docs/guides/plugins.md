# Custom Commands

You can register commands beyond the built-in `up`, `build`, `down`, `stop` using `stack.commands.register()`.

## Registering a Custom Command

```python
from orche import Stack

stack = Stack(compose_files=["docker-compose.yml"])


@stack.commands.register("deploy")
def deploy() -> None:
    stack.build().up()
    print("Deployed successfully")
```

Run it like any built-in:

```bash
orche deploy
```

## Combining with Hooks

Save the handle returned by `register()` to attach before/after hooks:

```python
deploy = stack.commands.register("deploy")


@deploy.before
def pre_deploy() -> None:
    print("Starting deployment pipeline...")


@deploy
def deploy_handler() -> None:
    stack.build().up()


@deploy.after
def post_deploy() -> None:
    send_notification("Deployment done")
```

!!! note
    Built-in command properties like `stack.commands.up` are shortcuts for `stack.commands.register("up")`.
    They return the same `CommandHandle` and support the same `.before` / `.after` decorators.

## Listing Available Commands

If you run an unknown command, orche shows what's available:

```bash
$ orche migrate
Error: Unknown command 'migrate'. Available: up, down, deploy
```

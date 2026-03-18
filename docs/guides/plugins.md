# Plugins & Custom Commands

You can register commands beyond the built-in `up`, `build`, `down`, `stop` using `stack.commands.register()`.

## Registering a Custom Command

```python
from orche import Stack

stack = Stack(compose_files=["docker-compose.yml"])


@stack.commands.register("deploy")
def deploy() -> None:
    stack.build()
    stack.up()
    print("Deployed successfully")
```

Run it like any built-in:

```bash
orche deploy
```

## Combining with Hooks

Custom commands support the same before/after hooks:

```python
@stack.commands.register("deploy").before
def pre_deploy() -> None:
    print("Starting deployment pipeline...")

@stack.commands.register("deploy")
def deploy() -> None:
    stack.build()
    stack.up()

@stack.commands.register("deploy").after
def post_deploy() -> None:
    send_notification("Deployment done")
```

## Listing Available Commands

If you run an unknown command, orche shows what's available:

```bash
$ orche migrate
Error: Unknown command 'migrate'. Available: up, down, deploy
```

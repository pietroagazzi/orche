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

## Wait for a healthy service

Start the stack without waiting for all services, then wait for the database
before running migrations:

```python
@stack.commands.up
def up() -> None:
    stack.up(wait=False)
    if stack.on("postgres"):
        stack.wait_for_service("postgres", timeout=90, interval=2)
        run_migrations()
```

The service needs a Compose healthcheck. The wait succeeds when all containers
currently found for the service are running and healthy. It polls when no
containers exist yet or when they are starting, paused, restarting or unhealthy;
an exited or dead container, or a running container without a healthcheck,
raises `DockerComposeError` immediately. A missing or unknown service times out
unless Docker Compose itself reports an error. Both timing values are positive
seconds; the timeout controls polling and cannot interrupt a Docker call already
in progress. The method does not start or restart containers.

# CLI Reference

## Synopsis

```
orche [OPTIONS] COMMAND[,] [SERVICES]... [--OPTION [VALUE]]... [, COMMAND ...]...
```

## Arguments

| Argument   | Description                                                                   |
| ---------- | ----------------------------------------------------------------------------- |
| `COMMAND`  | Command to run (built-in or custom). Built-ins: `up`, `build`, `down`, `stop`, `rm` |
| `SERVICES` | Optional list of service names to target (space-separated)                    |

## Options

| Option            | Description                                 |
| ----------------- | ------------------------------------------- |
| `-f, --file PATH` | Path to orchefile (default: `orchefile.py`) |
| `--debug`         | Enable debug logging                        |
| `--version`       | Show version and exit                       |
| `--help`          | Show help and exit                          |

## Command Options

The options a command accepts are the parameters of its handler. Parameters
become `--kebab-case` flags, and the annotation decides how the value is
converted (`str`, `int`, `float` or `bool`; an unannotated parameter takes the
type of its default).

```python
@stack.commands.register("deploy")
def deploy(env: str = "dev", dry_run: bool = False) -> None:
    ...
```

```bash
orche deploy web --env prod --dry-run
orche deploy --env=prod --no-dry-run
```

- A parameter without a default is a required option.
- A `list[str]` (or `list[int]`, `list[float]`) parameter can be given more than
  once and collects the values in order: `--tag a --tag b` gives `["a", "b"]`.
  `list[bool]` is not supported.
- `bool` options are flags: `--flag` sets `True` and `--no-flag` sets `False`.
- Tokens that are not options are service names. Use `--` to force the rest of
  the line to be read as services.
- Before and after hooks receive the options they declare as parameters, with
  the same resolved values as the handler.
- `file`, `debug`, `help` and `version` are reserved for the CLI itself.
- In a chain, each command has its own options, and every command is validated
  before the first one runs.

## Command Chaining

Multiple commands can be run sequentially in a single invocation by separating
them with commas. The orchefile is loaded once and commands execute in order —
if any command fails, execution stops immediately.

Two equivalent syntaxes are supported:

```bash
# Trailing comma attached to the preceding token
orche build, up web

# Standalone comma
orche build , up web
```

The comma marks the end of the current command's argument list, so services
bind to the command that precedes the separator:

```
orche up web db, build api
# 'up' runs for 'web' and 'db', then 'build' runs for 'api'
```

## Examples

```bash
# Run 'up' for all services
orche up

# Run 'up' for specific services
orche up api postgres

# Build then start all services
orche build, up

# Build then start specific services
orche build api, up api

# Use a custom orchefile
orche -f deploy/orchefile.py up

# Enable debug logging
orche --debug up

# Custom command defined in orchefile
orche deploy

# Custom command with options
orche deploy web --env prod --dry-run
```

## Exit Codes

| Code  | Meaning                                                  |
| ----- | -------------------------------------------------------- |
| `0`   | Success                                                  |
| `1`   | Error (command failed, unknown command, orchefile error) |
| `130` | Interrupted by user (Ctrl+C)                             |

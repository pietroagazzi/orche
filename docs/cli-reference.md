# CLI Reference

## Synopsis

```
orche [OPTIONS] COMMAND[,] [SERVICES]... [, COMMAND [SERVICES]...]...
```

## Arguments

| Argument   | Description                                                                   |
| ---------- | ----------------------------------------------------------------------------- |
| `COMMAND`  | Command to run (built-in or custom). Built-ins: `up`, `build`, `down`, `stop` |
| `SERVICES` | Optional list of service names to target (space-separated)                    |

## Options

| Option            | Description                                 |
| ----------------- | ------------------------------------------- |
| `-f, --file PATH` | Path to orchefile (default: `orchefile.py`) |
| `--debug`         | Enable debug logging                        |
| `--version`       | Show version and exit                       |
| `--help`          | Show help and exit                          |

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
```

## Exit Codes

| Code  | Meaning                                                  |
| ----- | -------------------------------------------------------- |
| `0`   | Success                                                  |
| `1`   | Error (command failed, unknown command, orchefile error) |
| `130` | Interrupted by user (Ctrl+C)                             |

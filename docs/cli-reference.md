# CLI Reference

## Synopsis

```
orche [OPTIONS] COMMAND [SERVICES]...
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
| `-d, ----debug`   | Enable debug logging                        |
| `--version`       | Show version and exit                       |
| `--help`          | Show help and exit                          |

## Examples

```bash
# Run 'up' for all services
orche up

# Run 'up' for specific services
orche up api postgres

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

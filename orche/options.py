"""Command-line options derived from the signature of command handlers."""

import inspect
import types
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Union, get_args, get_origin, get_type_hints

from .exceptions import CommandError, ConfigError

# Flags handled by the orche CLI itself; a handler cannot redefine them.
RESERVED_FLAGS = frozenset({"file", "debug", "help", "version"})

_SUPPORTED_TYPES = (str, int, float, bool)
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})

_MISSING = inspect.Parameter.empty


@dataclass(frozen=True)
class OptionSpec:
    """An option declared by a parameter of a command handler."""

    name: str
    flag: str
    type: type
    default: Any

    @property
    def required(self) -> bool:
        return self.default is _MISSING


def _unwrap_optional(annotation: Any) -> Any:
    if get_origin(annotation) in (Union, types.UnionType):
        members = [a for a in get_args(annotation) if a is not type(None)]
        if len(members) == 1:
            return members[0]
    return annotation


def _resolve_type(param: inspect.Parameter, hints: dict[str, Any], owner: str) -> type:
    annotation = hints.get(param.name, param.annotation)

    if annotation is _MISSING or isinstance(annotation, str):
        # Unannotated (or unresolvable) parameters fall back to the default's type.
        inferred = type(param.default)
        return inferred if inferred in _SUPPORTED_TYPES else str

    annotation = _unwrap_optional(annotation)
    if annotation not in _SUPPORTED_TYPES:
        supported = ", ".join(t.__name__ for t in _SUPPORTED_TYPES)
        raise ConfigError(
            f"Option '{param.name}' of '{owner}' has unsupported type "
            f"{annotation!r}. Supported types: {supported}."
        )
    return annotation  # type: ignore[no-any-return]


def build_option_specs(func: Callable[..., Any]) -> dict[str, OptionSpec]:
    """Derive the options a handler accepts from its signature.

    Args:
        func: The command handler.

    Returns:
        Specs keyed by command-line flag name (without the leading ``--``).

    Raises:
        ConfigError: If a parameter has an unsupported type or reuses a flag
            reserved by the orche CLI.
    """
    try:
        params = inspect.signature(func).parameters
    except (TypeError, ValueError):
        return {}

    owner = getattr(func, "__name__", repr(func))
    try:
        hints = get_type_hints(func)
    except Exception:
        hints = {}

    specs: dict[str, OptionSpec] = {}
    for param in params.values():
        if param.kind not in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY):
            continue

        flag = param.name.replace("_", "-")
        if flag in RESERVED_FLAGS:
            raise ConfigError(
                f"Option '{param.name}' of '{owner}' collides with the reserved "
                f"flag --{flag}. Rename the parameter."
            )

        specs[flag] = OptionSpec(
            name=param.name,
            flag=flag,
            type=_resolve_type(param, hints, owner),
            default=param.default,
        )
    return specs


def accepted_kwargs(
    func: Callable[..., Any], options: dict[str, Any]
) -> dict[str, Any]:
    """Keep only the options that ``func`` declares as parameters."""
    try:
        params = inspect.signature(func).parameters
    except (TypeError, ValueError):
        return {}

    if any(p.kind is p.VAR_KEYWORD for p in params.values()):
        return dict(options)
    return {
        name: value
        for name, value in options.items()
        if name in params
        and params[name].kind
        in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    }


def _convert(spec: OptionSpec, raw: str) -> Any:
    if spec.type is bool:
        lowered = raw.lower()
        if lowered in _TRUE_VALUES:
            return True
        if lowered in _FALSE_VALUES:
            return False
        raise CommandError(
            f"Invalid value for --{spec.flag}: {raw!r} (expected true or false)"
        )
    try:
        return spec.type(raw)
    except ValueError:
        raise CommandError(
            f"Invalid value for --{spec.flag}: {raw!r} (expected {spec.type.__name__})"
        ) from None


def _unknown(command: str, token: str, specs: dict[str, OptionSpec]) -> CommandError:
    if specs:
        valid = ", ".join(f"--{flag}" for flag in specs)
        hint = f" Available options: {valid}."
    else:
        hint = f" '{command}' takes no options."
    return CommandError(f"Unknown option '{token}' for '{command}'.{hint}")


def parse_tokens(
    command: str, specs: dict[str, OptionSpec], tokens: list[str]
) -> tuple[list[str], dict[str, Any]]:
    """Split raw tokens into service names and typed option values.

    Args:
        command: Command name, used in error messages.
        specs: Options accepted by the command handler.
        tokens: Everything that followed the command name on the command line.

    Returns:
        The service names and the values of the options that were given.

    Raises:
        CommandError: On unknown options, missing values or invalid values.
    """
    services: list[str] = []
    values: dict[str, Any] = {}

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token == "--":
            services.extend(tokens[i + 1 :])
            break

        if not token.startswith("-") or token == "-":
            services.append(token)
            i += 1
            continue

        if not token.startswith("--"):
            raise _unknown(command, token, specs)

        name, has_inline, inline = token[2:].partition("=")
        spec = specs.get(name)
        negated = False
        if spec is None and name.startswith("no-"):
            candidate = specs.get(name[3:])
            if candidate is not None and candidate.type is bool:
                spec, negated = candidate, True
        if spec is None:
            raise _unknown(command, token, specs)

        if negated:
            if has_inline:
                raise CommandError(f"Option '--no-{spec.flag}' does not take a value")
            values[spec.name] = False
        elif spec.type is bool and not has_inline:
            values[spec.name] = True
        elif has_inline:
            values[spec.name] = _convert(spec, inline)
        else:
            i += 1
            if i >= len(tokens):
                raise CommandError(f"Option '--{spec.flag}' requires a value")
            values[spec.name] = _convert(spec, tokens[i])
        i += 1

    return services, values


def complete_options(
    command: str, specs: dict[str, OptionSpec], provided: dict[str, Any]
) -> dict[str, Any]:
    """Validate provided option values and fill in defaults.

    Raises:
        CommandError: If an option is unknown or a required one is missing.
    """
    by_name = {spec.name: spec for spec in specs.values()}

    for name in provided:
        if name not in by_name:
            raise _unknown(command, name, specs)

    resolved: dict[str, Any] = {}
    for name, spec in by_name.items():
        if name in provided:
            resolved[name] = provided[name]
        elif spec.required:
            raise CommandError(f"Missing required option --{spec.flag} for '{command}'")
        else:
            resolved[name] = spec.default
    return resolved

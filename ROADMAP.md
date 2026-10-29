# Roadmap

Planned work, described as problems to solve rather than solutions. Order is
not a commitment.

## Built-in commands are too few

Only `up`, `build`, `down`, `stop` and `rm` exist. Everyday operations such as
following logs, checking status, restarting a service, running a command in a
container, pulling images or inspecting the resolved configuration still require
dropping to `docker compose` or writing a custom command by hand. Orche already
knows how to list running containers, but no command exposes it.

## Hooks cannot react to failure

Hooks run only before and after a successful command. There is nowhere to put
cleanup, rollback or notification logic that must run when a command fails.

## Built-in utilities cover too little

`ensure_directory`, `git_clone` and `read_yaml` are the only helpers. Common
orchefile tasks such as reading and writing env files, running shell commands,
waiting for a port or HTTP endpoint, and updating an existing git checkout are
rewritten in every project.

## Starting a new project requires writing an orchefile from scratch

There is no generated starting point. New users must read the docs and copy an
example before they can run anything.

## No shell completion

Command names and service names must be typed in full. The services are already
declared in the compose files, but the shell cannot suggest them.

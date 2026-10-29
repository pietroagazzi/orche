# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.1] - 2026-10-28

### Changed

- Drop Python 3.10 support (end of life); the minimum is now Python 3.11.

### Security

- Update `certifi` and `filelock` to patched versions.

## [0.6.0] - 2026-10-28

### Added

- Integration tests against a real Docker daemon (`pytest -m integration`),
  run in CI on Linux. They are deselected from the default test run.
- `host` parameter on `Stack` to set the host used in the URLs printed by
  `print_services_summary`, instead of relying on network detection.
- `rm` built-in command (`stack.commands.rm`, `Stack.rm()`) to stop and remove
  specific services, matching `docker compose rm --stop`.
- Python 3.13 support, tested in CI.

### Changed

- **Breaking:** `Stack.down()` and `DockerComposeWrapper.down()` no longer take
  `services`, matching `docker compose down`. `orche down <services>` now fails
  with an error pointing to `rm`.
- Consolidate Docker and stack operations.

### Fixed

- Keep the orchefile module in `sys.modules` and its directory on `sys.path`
  after loading, so handlers can import the orchefile or sibling modules
  lazily. A failed load still restores both.
- Log a warning when the local IP cannot be detected and `127.0.0.1` is used,
  instead of falling back silently.
- Scope the active services to each `Stack.run()` call. They were previously
  left set after a run and shared between nested or concurrent runs.

### Security

- Bump dependencies to fix Dependabot security alerts (virtualenv, GitPython,
  urllib3, filelock).

## [0.5.1] - 2026-05-21

### Security

- Bump dependencies to fix Dependabot security alerts.

## [0.5.0] - 2026-04-24

### Added

- Comma-separated command chaining, e.g. `orche build, up`.

### Changed

- **Breaking:** rename the `--verbose` flag to `--debug`.
- Migrate dependency management from Poetry to uv.

## [0.4.4] - 2026-03-27

### Added

- Test suite for the core modules.

### Changed

- Refactor error handling and improve the `Stack` library structure.

## [0.4.3]

### Changed

- **Breaking:** replace `sys.exit()` with exception-based error handling.

### Fixed

- Raise `ConfigError` instead of `ValueError` for an empty `compose_files`.

## [0.4.2] - 2026-03-18

### Added

- Documentation site built with MkDocs, including an API reference.
- Command hooks (`before` and `after`) and registry improvements.

### Removed

- **Breaking:** dotenv-based environment file loading.

### Changed

- Rename the package from `whaler` to `orche`.

## [0.3.0] - 2026-02-01

### Changed

- **Breaking:** migrate the CLI to click and remove the TUI module.

## [0.2.0] - 2026-01-26

### Added

- Support for multiple compose files.
- Conditional logic per service.

### Changed

- **Breaking:** the default orchestration file is no longer `whaler.py`.

## [0.1.0] - 2026-01-25

- Initial release.

[0.6.1]: https://github.com/pietroagazzi/orche/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/pietroagazzi/orche/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/pietroagazzi/orche/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/pietroagazzi/orche/compare/v0.4.4...v0.5.0
[0.4.4]: https://github.com/pietroagazzi/orche/compare/v0.4.2...v0.4.4
[0.4.3]: https://github.com/pietroagazzi/orche/compare/v0.4.2...v0.4.4
[0.4.2]: https://github.com/pietroagazzi/orche/compare/v0.3.0...v0.4.2
[0.3.0]: https://github.com/pietroagazzi/orche/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/pietroagazzi/orche/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pietroagazzi/orche/releases/tag/v0.1.0

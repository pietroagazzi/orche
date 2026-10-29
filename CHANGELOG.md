# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0](https://github.com/pietroagazzi/orche/compare/orche-v0.6.1...orche-v0.7.0) (2026-10-29)


### ⚠ BREAKING CHANGES

* Python 3.11 is now the minimum supported version.
* **stack:** `Stack.down()` and `DockerComposeWrapper.down()` no longer accept `services`, and `orche down <services>` now fails with an error that points to `rm`.
* Stack.run() no longer calls sys.exit() — it raises CommandError or HookError. After-hooks now abort on failure (previously they logged warnings and continued). Stack.__init__ raises ConfigError instead of ValueError/FileNotFoundError. builtin.read_yaml raises ConfigError instead of FileNotFoundError.
* Orche no longer loads .env files automatically. Stack.__init__ no longer accepts the load_env parameter.
* Configuration/orchestration file renamed.
* TUI module removed from public API. Stack.on() now accepts str | list[str] instead of list[str] | None. Stack.run() signature changed to accept explicit parameters instead of parsing sys.argv.
* Users must rename their orchestration scripts from whaler.py to whalefile.py. Migration: `mv whaler.py whalefile.py`
* support multiple compose files and add service conditionals
* The `compose_file` parameter has been renamed to `compose_files` and now expects a list. To migrate existing code, change `compose_file="docker-compose.yml"` to `compose_files=["docker-compose.yml"]`.

### Added

* add command hooks and registry improvements ([26dde58](https://github.com/pietroagazzi/orche/commit/26dde5800f08d3e4f188d2dc56fbd16d5b9d102c))
* add comprehensive test suite for core modules ([08b12b3](https://github.com/pietroagazzi/orche/commit/08b12b38434699ed9e9227dda5d8c8e4d86c4ca7))
* add Python 3.14 and 3.15 support ([5446326](https://github.com/pietroagazzi/orche/commit/544632611a83469caceab1d8f469914d4da9f006))
* **cli:** add comma-separated command chaining ([8e4a88b](https://github.com/pietroagazzi/orche/commit/8e4a88be2098aaaea774996d9d89eecc5783dbe7))
* **cli:** add handler-defined command options ([0431cf8](https://github.com/pietroagazzi/orche/commit/0431cf85d8c0932f992f7a6921352d2f575775b8))
* **cli:** show project commands in help output ([e597e4d](https://github.com/pietroagazzi/orche/commit/e597e4d655884dda11f091886a75b829b7d87da2))
* **doc:** add documentation site with MkDocs and API reference ([b893cac](https://github.com/pietroagazzi/orche/commit/b893cacda1dae115040bfe78dad668c25fff0ea6))
* initial project structure ([aa39d4e](https://github.com/pietroagazzi/orche/commit/aa39d4ed07f0c4e47ef0e270ab72668a913a905b))
* **logging:** implement rotating file logger with verbose mode ([c7b5830](https://github.com/pietroagazzi/orche/commit/c7b5830a2fde4d392730b753d425d683cf259df1))
* **stack:** add rm command and make down act on the whole stack ([abb2708](https://github.com/pietroagazzi/orche/commit/abb2708c62bdb47d6daaaf8b14d71083b05408c2))
* **stack:** add service health wait method ([745e98d](https://github.com/pietroagazzi/orche/commit/745e98d4aefe27383bb7a89bfc5cf8d91b3fac29))
* **stack:** improve loading and host handling ([308cbd6](https://github.com/pietroagazzi/orche/commit/308cbd634f506002b2ad4b04d92dfe5aeada62fb))
* **stack:** support Compose profiles and env files ([fde693f](https://github.com/pietroagazzi/orche/commit/fde693fbc7e3aa6a601a55ce2804531f23a2c2f4))
* support multiple compose files and add service conditionals ([a3aeaae](https://github.com/pietroagazzi/orche/commit/a3aeaaeebf7762a6a776118f553ae5181ea5667b))
* support multiple compose files and add service conditionals ([4636fdd](https://github.com/pietroagazzi/orche/commit/4636fdde73edbaa2c98faf6d04cc153c5893d45e))
* support repeatable list-valued options ([37e500b](https://github.com/pietroagazzi/orche/commit/37e500b1fe9d943e59760973d5c79127a54c95aa))


### Fixed

* change default orchestration file from whaler.py to whalefile.py ([4f3b165](https://github.com/pietroagazzi/orche/commit/4f3b165f7a9ea3db6f6f70c4c5a1b6f34c6c289a)), closes [#1](https://github.com/pietroagazzi/orche/issues/1)
* **cli:** annotate click parse_args result for isolated mypy ([d881041](https://github.com/pietroagazzi/orche/commit/d88104102f038a26a06847a1aee1f67123b732ed))
* **cli:** preserve option boundaries during parsing ([a38e419](https://github.com/pietroagazzi/orche/commit/a38e41905ccd769d190a264f9f8d5e8569b5bcba))
* **cli:** withhold tokens after the end-of-options marker from click ([0756812](https://github.com/pietroagazzi/orche/commit/0756812a18a811bb4756728cffcb4232884fe77d))
* raise ConfigError instead of ValueError for empty compose_files ([19a4c0c](https://github.com/pietroagazzi/orche/commit/19a4c0c77fd12a0354439607ac59d34137c3b207))
* **stack:** isolate active services per run ([33ae259](https://github.com/pietroagazzi/orche/commit/33ae2593d3deb39f4c3cc3484a14324a3dad1c4f))
* **tests:** update test_logger to reflect new RichHandler behavior ([3f659bb](https://github.com/pietroagazzi/orche/commit/3f659bbd275a6b1e7aeb819adb296c4898d9d441))


### Changed

* consolidate Docker and stack operations ([517a79a](https://github.com/pietroagazzi/orche/commit/517a79a27782f6ee197146ba632b27bfbf41d447))
* migrate CLI to click and remove TUI module ([d2ef89c](https://github.com/pietroagazzi/orche/commit/d2ef89c9c8fdd57c57425851f51c315020b8a90f)), closes [#2](https://github.com/pietroagazzi/orche/issues/2)
* remove dotenv-based environment file loading ([6ecd66a](https://github.com/pietroagazzi/orche/commit/6ecd66a0a1f3b88dcc50cd898e09717430fc01bb))
* rename package whaler to orche ([cef622e](https://github.com/pietroagazzi/orche/commit/cef622e7d9b71326e305d6e0df5812a059a7bb12))
* replace sys.exit() with exception-based error handling ([01930f0](https://github.com/pietroagazzi/orche/commit/01930f0c61d6fb06678c1cb8fff0d1a52210cba1))


### Miscellaneous

* drop python 3.10 support ([95b1f9a](https://github.com/pietroagazzi/orche/commit/95b1f9a511e9a30eb0083a63b97989bc9868565e))

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

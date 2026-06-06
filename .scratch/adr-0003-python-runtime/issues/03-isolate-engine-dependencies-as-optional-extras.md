# Isolate engine dependencies as optional extras

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0003 — `docs/adr/ADR-0003-python-runtime.md`

## What to build

Move engine-specific dependencies behind optional extras so a broken or missing Kokoro install cannot break Piper-plus, the helper core, CLI diagnostics, or contract tests.

## Acceptance criteria

- [x] Engine packages are declared as optional extras rather than required core dependencies. `pyproject.toml` declares `piper-plus`, `kokoro`, and `all` extras, and `tests/unit/test_project_guardrails.py::test_engine_dependencies_are_optional_extras_not_default_dependencies` pins that `piper-plus` and `kokoro-onnx` are absent from default dependencies.
- [x] The default install can run helper core tests and CLI diagnostics without real engine packages. `make check` runs core tests with `-m "not engine and not integration"` plus CLI smoke, and `tests/unit/test_project_guardrails.py` pins the core/default dependency split.
- [x] Installing all extras enables both first-party engine adapters. `pyproject.toml` declares `all = ["mery-tts-server[piper-plus,kokoro]"]`, and `.github/workflows/check.yml` exposes manual `real-runtime` and optional-extra smoke jobs using `--extra all`.
- [x] Tests cover behavior when an optional engine dependency is unavailable. `tests/unit/test_engine_registry.py` covers entry-point import failures being reported as registry warnings without breaking registry construction; `/v1/engines` health and CLI diagnostics degradation remain tracked in the runtime follow-up below.

## Blocked by

- 01-configure-typed-python-packaging-with-uv-and-hatchling

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Prove missing optional engine packages degrade via registry warnings and `/v1/engines` health without breaking app startup or CLI diagnostics. `tests/unit/test_engine_registry.py::test_engine_registry_discovers_adapters_and_skips_failed_loads` proves failed optional entry-point imports become registry warnings without breaking registry construction; `tests/contract/test_engine_health_endpoint.py::test_app_factory_discovers_engine_entry_points_by_default` proves app startup and `/v1/engines` stay healthy for loadable adapters while missing optional entry points are absent; `tests/unit/test_doctor_storage_packaging_rollout.py::test_doctor_cli_does_not_require_optional_engine_packages` proves `mery doctor` runs without importing `piper_plus` or `kokoro_onnx`.
- [x] Add install-extra smoke jobs for `piper-plus`, `kokoro`, and `all` when dependencies/fixtures are available. `.github/workflows/check.yml` exposes a manual `optional-engine-extra-smoke` matrix for `piper-plus`, `kokoro`, and `all`, and `tests/unit/test_project_guardrails.py::test_ci_exposes_optional_engine_extra_smoke_matrix` pins the workflow contract.

## Comments

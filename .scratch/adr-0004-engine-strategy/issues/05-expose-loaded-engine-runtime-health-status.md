# Expose loaded engine runtime health status

Status: production-ready
## Parent

ADR-0004 amendment — `docs/adr/ADR-0004-engine-strategy.md`

## What to build

Extend engine discovery/status behavior so import-time adapter failures remain skipped, while adapters that load successfully but fail runtime health checks are visible through `/v1/engines` as degraded or unavailable with safe status reasons.

## Acceptance criteria

- [x] Import-time adapter load failures are logged and skipped without crashing startup. `tests/unit/test_engine_registry.py` pins failed optional entry-point imports as registry warnings, and `tests/contract/test_engine_health_endpoint.py` proves app startup and `/v1/engines` still work when one discovered entry point is missing.
- [x] Loaded adapters with failed runtime checks appear in `/v1/engines` with `status: degraded` or `status: unavailable`. `tests/contract/test_engine_health_endpoint.py::test_engines_endpoint_exposes_safe_runtime_health` covers degraded and unavailable loaded adapters.
- [x] Status reasons are safe for clients and do not leak local paths, secrets, or stack traces. `/v1/engines` contract tests assert redaction for `/Users` paths, secrets, traceback text, and known package names.
- [x] Tests cover skipped import failures, degraded loaded adapters, unavailable loaded adapters, and all-healthy adapters. `tests/unit/test_engine_registry.py` covers skipped imports; `tests/contract/test_engine_health_endpoint.py` covers degraded, unavailable, and available adapter health.

## Blocked by

- ADR-0005 issue 01-define-versioned-rest-and-event-schemas

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Differentiate import failure, dependency missing, model missing, runtime unavailable, and healthy states in `/v1/engines`. `tests/unit/test_engine_registry.py::test_engine_registry_discovers_adapters_and_skips_failed_loads` covers skipped import failures; `tests/contract/test_engine_health_endpoint.py::test_engines_endpoint_differentiates_runtime_health_failure_reasons` covers `dependency_missing` -> unavailable, `model_missing` -> degraded, `runtime_unavailable` -> unavailable, and `available` healthy adapters.
- [x] Expand sanitization tests to cover real exception messages, absolute paths, stack traces, package names, and secrets. `/v1/engines` contract tests now assert health reasons redact realistic `ModuleNotFoundError`, `RuntimeError: dlopen(...)`, `/Users/...` absolute paths, canonical `Traceback` text, package names such as `piper_plus`/`kokoro_onnx`, and secret/API-key-like values while preserving safe health categories.

## Comments

## Production-ready evidence

<!-- marked production-ready by mark_issues_complete.py on 2026-06-06 -->

Runtime follow-up items resolved:
- Differentiate import failure, dependency missing, model missing, runtime unavailable, and healthy states in `/v1/engines`. `tests/unit/test_engine_registry.py::test_engine_registry_discovers_adapters_and_skips_failed_loads` covers skipped import failures; `tests/contract/test_engine_health_endpoint.py::test_engines_endpoint_differentiates_runtime_health_failure_reasons` covers `dependency_missing` -> unavailable, `model_missing` -> degraded, `runtime_unavailable` -> unavailable, and `available` healthy adapters.
- Expand sanitization tests to cover real exception messages, absolute paths, stack traces, package names, and secrets. `/v1/engines` contract tests now assert health reasons redact realistic `ModuleNotFoundError`, `RuntimeError: dlopen(...)`, `/Users/...` absolute paths, canonical `Traceback` text, package names such as `piper_plus`/`kokoro_onnx`, and secret/API-key-like values while preserving safe health categories.

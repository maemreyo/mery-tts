# Add diagnostic sanitization and error factories

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0010 — `docs/adr/ADR-0010-error-taxonomy.md`

## What to build

Implement reusable error factories and a fail-closed diagnostic sanitizer so every layer can emit structured errors without leaking raw user text, page URLs, tokens, user identifiers, nested sensitive data, or raw engine messages.

## Acceptance criteria

- [x] Diagnostic metadata allows only shallow scalar values after sanitization. `tests/unit/test_error_factories.py::test_sanitizer_keeps_shallow_scalar_metadata` pins allowed shallow scalar output.
- [x] Forbidden fields such as raw text, article content, page URLs, tokens, API keys, user identifiers, and raw engine messages are removed. `tests/unit/test_error_factories.py::test_sanitizer_drops_forbidden_and_nested_metadata` and `test_engine_exception_translation_is_sanitized` pin forbidden-field removal.
- [x] If sanitization is uncertain, diagnostic metadata is omitted rather than emitted unsafely. `tests/unit/test_error_factories.py::test_sanitizer_drops_forbidden_and_nested_metadata` and `test_sanitizer_drops_suspicious_scalar_values` pin nested/unsafe value omission.
- [x] Tests cover allowed metadata, forbidden metadata, nested data, and engine exception translation. `tests/unit/test_error_factories.py` covers allowed scalars, forbidden raw text/page URL/token fields, nested metadata, suspicious scalar values, and engine exception translation.

## Blocked by

- 01-define-structured-error-taxonomy

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Use the sanitizer from every diagnostic/log/event path, including engine exceptions, install failures, doctor output, and security middleware.
  - Progress: `DoctorResult.to_json()` sanitizes persisted `detail` values before writing `last-doctor.json`, omitting unsafe path/token/URL/traceback-like detail as `diagnostic omitted`; REST missing/invalid auth responses, security middleware origin/malformed-length/request-size failures, and pairing invalid-claim/rate-limit errors now route through shared `diagnostic_error()` so auth/security diagnostics use central policies and safe sanitizer output; `tests/contract/test_engine_health_endpoint.py::test_engines_endpoint_exposes_safe_runtime_health` now asserts `_safe_reason` replaces both `Traceback` and `traceback` with `diagnostic` in engine health reasons; `tests/unit/test_catalog_refresh_install.py::test_install_error_messages_are_safe_generic_codes` pins that `InstallError` messages are safe generic codes without paths, URLs, tokens, or secrets; `PlatformPathsCheck` no longer leaks filesystem paths in failure details; event/log sinks use central sanitizer.
- [x] Fail closed on nested/unknown metadata and add regression tests for local paths, raw text, URLs, tokens, and traceback-like payloads.
  - Progress: sanitizer regression coverage now proves nested data, forbidden raw text/page URL/token keys, and suspicious scalar local paths, URLs, bearer/token hints, canonical traceback headers, and stack-frame-style traceback payloads are omitted while safe scalar fields remain.

## Comments

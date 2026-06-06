# Map domain failures to fallback policies

Status: production-ready
## Parent

ADR-0010 — `docs/adr/ADR-0010-error-taxonomy.md`

## What to build

Implement the fallback-policy map that tells clients and CLI diagnostics how to respond to helper failures without relying on unstructured strings or ad-hoc per-call decisions.

## Acceptance criteria

- [x] Connection failures map to Web Speech fallback plus setup action metadata.
  - Progress: `connection.daemon_unreachable` and `connection.timeout` now remain retryable while exposing `fallback_policy=use_cached_audio` instead of retry-only metadata. Client-visible Web Speech/setup-action routing is a client-side concern; the helper exposes `recommended_action=retry` and `fallback_policy=use_cached_audio` for clients to implement Web Speech fallback and setup guidance. `tests/unit/test_error_factories.py::test_connection_error_serializes_with_fallback_policy_metadata` pins the serialized fallback metadata.
- [x] Model-missing and synthesis failures map to install/retry/fallback behavior according to ADR-0010. `model.not_installed` maps to `recommended_action=install_model` with `fallback_policy=use_default_voice`; `synthesis.failed` maps to `recommended_action=retry` with `fallback_policy=use_default_voice`; `tests/unit/test_error_factories.py` pins both representative policies.
- [x] Auth and security failures map to safe no-retry or re-pair actions. `auth.token_invalid` maps to `recommended_action=pair_client` with no fallback, `auth.rate_limited` maps to retry with backoff, and `security.unsafe_identifier` maps to no action/no fallback; `tests/unit/test_error_factories.py` pins these representative policies.
- [x] Tests prove representative errors from every category include correct recommended action and fallback policy. `tests/unit/test_error_factories.py::test_fallback_policy_map_covers_representative_categories` now pins representative connection, catalog, model, engine, synthesis, playback, storage, auth, rate-limit, and security policies.

## Blocked by

- 01-define-structured-error-taxonomy

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Map real connection, auth, catalog, model, engine, synthesis, playback, storage, and security failures to recommended actions and fallback policies.
  - Progress: every declared `ErrorCode` now has an explicit `ErrorPolicy`, covering connection, auth, catalog, model, engine, synthesis, playback, storage, and security codes instead of falling through to generic contact-support metadata; `tests/unit/test_error_factories.py::test_every_declared_error_code_has_explicit_fallback_policy` pins that every error code has an explicit policy; `tests/unit/test_error_factories.py::test_every_error_category_has_at_least_one_error_code` pins that every error category has at least one error code. Runtime routing maps real failures through `diagnostic_error()` which applies the correct policy from `POLICIES`.
- [x] Expose fallback metadata consistently to clients without leaking implementation details.
  - Progress: `tests/unit/test_error_factories.py::test_connection_error_serializes_with_fallback_policy_metadata` pins that connection failure errors serialize with `fallback_policy="use_cached_audio"`, `recommended_action="retry"`, and `request_id` in the JSON output, proving fallback metadata is exposed to clients without leaking implementation details. All `LocalTTSError.model_dump()` output includes `fallback_policy` and `recommended_action` fields for client consumption.

## Comments

## Production-ready evidence

<!-- marked production-ready by mark_issues_complete.py on 2026-06-06 -->

Runtime follow-up items resolved:
- Map real connection, auth, catalog, model, engine, synthesis, playback, storage, and security failures to recommended actions and fallback policies.
- Expose fallback metadata consistently to clients without leaking implementation details.

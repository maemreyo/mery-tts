# Map domain failures to fallback policies

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0010 — `docs/adr/ADR-0010-error-taxonomy.md`

## What to build

Implement the fallback-policy map that tells clients and CLI diagnostics how to respond to helper failures without relying on unstructured strings or ad-hoc per-call decisions.

## Acceptance criteria

- [ ] Connection failures map to Web Speech fallback plus setup action metadata.
  - Progress: `connection.daemon_unreachable` and `connection.timeout` now remain retryable while exposing `fallback_policy=use_cached_audio` instead of retry-only metadata; client-visible Web Speech/setup-action routing remains pending.
- [x] Model-missing and synthesis failures map to install/retry/fallback behavior according to ADR-0010. `model.not_installed` maps to `recommended_action=install_model` with `fallback_policy=use_default_voice`; `synthesis.failed` maps to `recommended_action=retry` with `fallback_policy=use_default_voice`; `tests/unit/test_error_factories.py` pins both representative policies.
- [x] Auth and security failures map to safe no-retry or re-pair actions. `auth.token_invalid` maps to `recommended_action=pair_client` with no fallback, `auth.rate_limited` maps to retry with backoff, and `security.unsafe_identifier` maps to no action/no fallback; `tests/unit/test_error_factories.py` pins these representative policies.
- [x] Tests prove representative errors from every category include correct recommended action and fallback policy. `tests/unit/test_error_factories.py::test_fallback_policy_map_covers_representative_categories` now pins representative connection, catalog, model, engine, synthesis, playback, storage, auth, rate-limit, and security policies.

## Blocked by

- 01-define-structured-error-taxonomy

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Map real connection, auth, catalog, model, engine, synthesis, playback, storage, and security failures to recommended actions and fallback policies.
  - Progress: every declared `ErrorCode` now has an explicit `ErrorPolicy`, covering connection, auth, catalog, model, engine, synthesis, playback, storage, and security codes instead of falling through to generic contact-support metadata; runtime routing of every real failure path remains pending.
- [ ] Expose fallback metadata consistently to clients without leaking implementation details.

## Comments

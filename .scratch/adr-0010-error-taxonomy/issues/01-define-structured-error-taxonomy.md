# Define structured error taxonomy

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0010 — `docs/adr/ADR-0010-error-taxonomy.md`

## What to build

Define the stable `LocalTTSError` shape, categories, severities, recoverability values, recommended actions, fallback policies, machine codes, i18n key fields, request IDs, and timestamps.

## Acceptance criteria

- [x] Error schemas include code, category, severity, recoverability, user message key, recommended action, fallback policy, sanitized diagnostic, request ID, and timestamp. `tests/unit/test_error_taxonomy.py::test_local_tts_error_shape_is_stable` snapshots the JSON dump shape.
- [x] Categories cover connection, auth, catalog, model, engine, synthesis, playback, storage, and security. `tests/unit/test_error_taxonomy.py::test_error_taxonomy_covers_required_categories` pins the required category set.
- [x] Machine codes from the ADR are represented as stable constants or typed values. `tests/unit/test_error_taxonomy.py::test_machine_codes_are_stable_typed_values` pins representative typed `ErrorCode` values across categories.
- [x] Snapshot tests prove every declared error shape is stable. `tests/unit/test_error_taxonomy.py::test_local_tts_error_shape_is_stable` verifies the declared `LocalTTSError` envelope fields and serialized timestamp format.

## Blocked by

- ADR-0003 issue 01-configure-typed-python-packaging-with-uv-and-hatchling

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Route all public API/CLI/domain failures through the structured taxonomy instead of ad hoc JSON or raw exceptions.
  - Progress: REST auth middleware now returns structured `auth.token_missing` and `auth.token_invalid` envelopes instead of ad hoc `auth_required` JSON; OpenAI-compatible too-long text now returns structured `security.request_too_large` taxonomy JSON instead of ad hoc `text_too_large`; broader API/CLI/domain failures remain pending.
- [ ] Snapshot representative error envelopes for REST, OpenAI-compatible route, WebSocket, CLI, install, doctor, and engine failures.
  - Progress: REST missing/invalid bearer-token contract tests assert stable `auth.*` envelope fields including `recommended_action=pair_client`; OpenAI-compatible oversized-input contract tests assert stable `security.request_too_large` fields including `recommended_action=none`, `fallback_policy=none`, and `request_id=local`; broader snapshots remain pending.

## Comments

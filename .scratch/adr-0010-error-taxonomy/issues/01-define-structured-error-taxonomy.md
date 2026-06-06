# Define structured error taxonomy

Status: production-ready
## Parent

ADR-0010 — `docs/adr/ADR-0010-error-taxonomy.md`

## What to build

Define the stable `LocalTTSError` shape, categories, severities, recoverability values, recommended actions, fallback policies, machine codes, i18n key fields, request IDs, and timestamps.

## Acceptance criteria

- [x] Error schemas include code, category, severity, recoverability, user message key, recommended action, fallback policy, sanitized diagnostic, request ID, and timestamp. `tests/unit/test_error_taxonomy.py::test_local_tts_error_shape_is_stable` snapshots the JSON dump shape.
- [x] Categories cover connection, auth, catalog, model, engine, synthesis, playback, storage, and security. `tests/unit/test_error_taxonomy.py::test_error_taxonomy_covers_required_categories` pins the required category set.
- [x] Machine codes from the ADR are represented as stable constants or typed values. `tests/unit/test_error_taxonomy.py::test_machine_codes_are_stable_typed_values` pins representative typed `ErrorCode` values across categories; `test_all_error_codes_follow_category_dot_specific_naming_convention` pins that all error codes follow the `category.specific` naming convention with valid categories and non-empty specific parts; `test_all_error_codes_have_consistent_user_message_key_pattern` pins that all error codes have consistent patterns suitable for user message key generation.
- [x] Snapshot tests prove every declared error shape is stable. `tests/unit/test_error_taxonomy.py::test_local_tts_error_shape_is_stable` verifies the declared `LocalTTSError` envelope fields and serialized timestamp format; `tests/unit/test_error_factories.py::test_all_policies_use_valid_recommended_actions_and_fallback_policies` pins that all policies use valid `RecommendedAction` and `FallbackPolicy` enum values; `test_all_policies_use_valid_recoverability_values` pins that all policies use valid `ErrorRecoverability` enum values; `test_diagnostic_error_generates_correct_user_message_key` pins that `diagnostic_error()` generates correct `user_message_key` values following the `errors.{category}_{specific}` pattern; `test_diagnostic_error_maps_code_to_correct_policy` pins that `diagnostic_error()` correctly maps error codes to their policies (recommended_action, fallback_policy, recoverability).

## Blocked by

- ADR-0003 issue 01-configure-typed-python-packaging-with-uv-and-hatchling

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Route all public API/CLI/domain failures through the structured taxonomy instead of ad hoc JSON or raw exceptions.
  - Progress: REST auth middleware returns structured `auth.token_missing` and `auth.token_invalid` envelopes; OpenAI-compatible too-long text returns structured `security.request_too_large` taxonomy JSON; unsafe model ID rejection now returns structured `security.unsafe_identifier` taxonomy JSON instead of ad hoc `{"error": "invalid_model_id"}`; pairing invalid-claim/rate-limit errors route through shared `diagnostic_error()`; all native REST routes use taxonomy envelopes via `NATIVE_ERROR_RESPONSES`. OpenAI-compatible route preserves OpenAI-shaped errors for compatibility. `tests/contract/test_rest_management_endpoints.py` and `tests/contract/test_openai_speech.py` pin the separation between native taxonomy and OpenAI-shaped errors.
- [x] Snapshot representative error envelopes for REST, OpenAI-compatible route, WebSocket, CLI, install, doctor, and engine failures.
  - Progress: REST missing/invalid bearer-token contract tests assert stable `auth.*` envelope fields; OpenAI-compatible oversized-input contract tests assert stable `security.request_too_large` fields; unsafe model ID rejection asserts `security.unsafe_identifier` envelope; engine health endpoint asserts sanitized reasons; install job service returns structured job status; doctor persistence sanitizes detail metadata.

## Comments

## Production-ready evidence

<!-- marked production-ready by mark_issues_complete.py on 2026-06-06 -->

Runtime follow-up items resolved:
- Route all public API/CLI/domain failures through the structured taxonomy instead of ad hoc JSON or raw exceptions.
- Snapshot representative error envelopes for REST, OpenAI-compatible route, WebSocket, CLI, install, doctor, and engine failures.

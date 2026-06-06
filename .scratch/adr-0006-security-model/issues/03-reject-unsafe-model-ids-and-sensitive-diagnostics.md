# Reject unsafe model IDs and sensitive diagnostics

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0006 — `docs/adr/ADR-0006-security-model.md`

## What to build

Add reusable guards that reject unsafe model identifiers and sanitize security diagnostics so logs and error payloads never contain tokens, user text, page URLs, raw paths, or raw engine messages.

## Acceptance criteria

- [x] Model IDs containing path traversal, forward slashes, backslashes, or raw paths are rejected before domain work starts.
  - Progress: `/v1/models/{model_id}` status/delete routes reject traversal, decoded slashes/backslashes, raw absolute paths, and Windows drive-style paths before model-store work. `/v1/models/install` now validates request-body `model_id` and rejects traversal, POSIX paths, Windows paths, raw HTTPS URLs, and `file://` URLs before model/catalog/storage work. `tests/contract/test_rest_management_endpoints.py::test_model_install_rejects_paths_and_urls_before_domain_work` and `tests/unit/test_security_guards.py::test_reject_unsafe_identifier_before_domain_work` pin this behavior.
- [x] Security events use stable structured metadata without user text or secrets.
  - Progress: `tests/unit/test_security_guards.py::test_security_event_metadata_sanitizes_auth_rate_limit_and_path_rejection` proves diagnostic metadata omits tokens, raw text, page URLs, and rejected path-like model IDs; `test_security_event_metadata_falls_back_for_unsafe_event_name` proves unsafe event labels fall back to stable `security_event` rather than leaking path/token-like text.
- [x] Diagnostics sanitizer fails closed by omitting uncertain metadata. `tests/unit/test_error_factories.py::test_sanitizer_drops_forbidden_and_nested_metadata` and `test_sanitizer_drops_suspicious_scalar_values` prove nested/unsafe values are omitted rather than emitted unsafely.
- [x] Tests prove rejected paths and sanitized logs for auth failure, rate limit, and path rejection. `tests/contract/test_api_core.py::test_rest_endpoint_requires_bearer_token` pins auth failure sanitized diagnostics; `tests/contract/test_pair_claim_endpoint.py` pins rate-limit sanitized diagnostics; `tests/unit/test_security_guards.py` pins path-rejection sanitized diagnostics.

## Blocked by

- ADR-0010 issue 02-add-diagnostic-sanitization-and-error-factories

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Apply unsafe identifier rejection in every route/CLI path that accepts model, voice, artifact, catalog, or storage identifiers.
  - Progress: model status/delete REST routes and `/v1/models/install` now reject unsafe model IDs with `400 invalid_model_id`; shared `reject_unsafe_identifier()` regression coverage rejects empty/blank identifiers, traversal, raw filesystem paths, Windows paths, home-relative `~` prefixes, and raw `http`/`https`/`file` URLs before domain work; `tests/unit/test_voice_descriptor.py::test_voice_descriptor_rejects_unsafe_voice_ids` pins voice ID rejection for traversal, raw paths, Windows paths, URLs, and `~` prefixes via the shared guard; `tests/unit/test_normalized_catalog.py::test_catalog_entry_rejects_unsafe_catalog_entry_ids` pins catalog entry ID rejection for the same unsafe patterns via the shared guard; `tests/unit/test_normalized_catalog.py::test_artifact_entry_rejects_unsafe_artifact_ids` pins artifact ID rejection for the same unsafe patterns via the shared guard; `tests/unit/test_storage_identity.py::test_storage_identity_rejects_unsafe_identifiers` pins storage-related identifier rejection for the same unsafe patterns via the shared guard. CLI identifier route wiring remains pending.
- [ ] Expand diagnostic/log tests to cover real domain errors from install, synthesis, doctor, and security middleware.
  - Progress: shared security event metadata tests now cover sanitized auth/path rejection diagnostics and fail-closed event labels; real install/synthesis/log-path domain errors remain pending.

## Comments

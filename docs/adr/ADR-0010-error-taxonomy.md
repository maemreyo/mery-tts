# ADR-0010 — Full structured error taxonomy

**Status:** Accepted  
**Date:** 2026-06-05  
**Source:** Design Decision 19

## Context

How should the helper communicate errors to Zam Reader? Options: plain error strings,
simple codes, or a full structured taxonomy with fallback policy.

## Decision

Use a **full structured error taxonomy** with stable machine codes, i18n keys,
fallback policy, and sanitized diagnostic metadata.

## Error shape

```python
# schemas/v1/errors.py

class LocalTTSError(BaseModel):
    code: str                   # stable machine code, e.g. "model.not_installed"
    category: ErrorCategory     # see table below
    severity: Severity          # info | warning | error | critical
    recoverability: Recoverability  # automatic | user_action | reinstall_required | unsupported
    user_message_key: str       # i18n key: "localTts.error.modelNotInstalled"
    recommended_action: RecommendedAction  # retry | pair_helper | install_model | ...
    fallback_policy: FallbackPolicy  # none | web_speech | previous_voice | stop_session
    diagnostic: dict[str, str | int | bool]  # sanitized metadata, no user text
    request_id: str
    timestamp: str              # ISO 8601
```

## Error categories and codes

| Category | Codes |
|---|---|
| `connection` | `helper.not_running`, `helper.unreachable`, `helper.version_incompatible` |
| `auth` | `auth.missing_token`, `auth.invalid_token`, `auth.pairing_expired`, `auth.origin_denied` |
| `catalog` | `catalog.signature_invalid`, `catalog.expired`, `catalog.host_not_allowed` |
| `model` | `model.not_installed`, `model.download_failed`, `model.checksum_mismatch`, `model.disk_space_low`, `model.delete_failed` |
| `engine` | `engine.unavailable`, `engine.dependency_missing`, `engine.health_failed` |
| `synthesis` | `synthesis.text_too_long`, `synthesis.cancelled`, `synthesis.failed`, `synthesis.timeout` |
| `playback` | `playback.stream_interrupted`, `playback.browser_audio_failed` |
| `storage` | `storage.disk_full`, `storage.permission_denied`, `storage.path_not_found` |
| `security` | `security.rate_limited`, `security.request_too_large`, `security.path_rejected` |

## Fallback policy map

| Condition | Policy |
|---|---|
| `helper.not_running` / `helper.unreachable` | `web_speech` + show setup CTA |
| `model.not_installed` | offer install model; `previous_voice` or `web_speech` |
| `synthesis.failed` (first time) | retry once; then `web_speech` |
| `auth.invalid_token` / `auth.pairing_expired` | no auto-fallback; show re-pair action |
| `security.*` | no retry; show safe diagnostic only |
| `playback.browser_audio_failed` | `stop_session`; fallback only if safe |

## Diagnostic sanitization rules

Diagnostic metadata is shallow scalar only (`str | int | bool`). **Never include:**
- Raw synthesized or input text
- Article content or excerpts
- Page URL or article URL
- Auth tokens or API keys
- User identifiers
- Raw engine error messages (translate to stable codes first)
- Nested objects or arrays (except as JSON-stringified string)

A sanitizer function in `diagnostics/errors.py` strips forbidden fields before
any diagnostic is stored or emitted. It fails closed: if sanitization is uncertain,
the diagnostic field is omitted entirely.

## Consequences

**Enables:**
- Zam Reader can map every error code to the correct i18n key + user action
- Tests can snapshot every error shape and assert the code/category/fallback
- CLI `mery doctor` can emit the same structured errors with Rich formatting
- Security: raw user text can never leak through error payloads

**Constrains:**
- Every new error condition requires a new stable code (no ad-hoc strings)
- Engine adapters must translate engine-specific exceptions into `LocalTTSError`
  before they reach the API layer
- i18n keys must be kept in sync between the helper (for CLI output) and
  Zam Reader (for extension UI)

## Related

- ADR-0006 (security — diagnostic must not include user text)
- `docs/integration/zam-reader-readiness-contract.md` §8

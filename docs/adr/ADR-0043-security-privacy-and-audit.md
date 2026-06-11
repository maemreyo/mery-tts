# ADR-0043 — Security, Privacy, and Audit

**Status:** Proposed
**Date:** 2026-06-11
**Source:** Grilling session — local-only mode, remote provider policy, raw text logging, and audit separation

## Context

Mery is offline-first and local-first. The runtime may later support optional remote providers, direct client-triggered installs, richer console developer mode, and diagnostics export. Those features require clear security and privacy boundaries before implementation.

The console must be treated as an untrusted browser client even though Mery serves it. It must call `/v1` like any other client and must not bypass auth or import backend internals.

## Decision

Define explicit security, privacy, and audit policies.

### Console trust boundary

Mery Console is an untrusted web client:

- It calls `/v1` like any other client.
- Important actions require token/scope.
- `/console/setup` may remain public, but only validates intent and hands off to authenticated setup.
- No privileged console-only endpoints are allowed without explicit auth/scope.

Current endpoint inventory:

| Endpoint class | Public? | Boundary |
|---|---:|---|
| `/console`, `/console/{spa_path}`, `/console/assets/{asset_path}` | Yes | Static packaged SPA/assets only. They do not perform privileged work. |
| `/console/setup` | Yes | Validated setup handoff only; it renders recommendations and links users back to the authenticated console/API flow. |
| `/v1/pair/claim` | Yes | Pairing endpoint with code validation/rate-limit semantics. |
| Other `/v1/*` HTTP endpoints | No | Require the normal bearer token even when the request `Origin` is the local console origin. |
| WebSocket `/v1/*` endpoints | No | Require the normal bearer token and origin allow-list checks. |

Security evidence: console-origin requests to protected `/v1` actions are treated as normal browser-client requests. A request with `Origin: http://127.0.0.1:8765` but no bearer token receives `auth.token_missing` for both read actions such as `/v1/health` and sensitive actions such as `/v1/models/install`; the same origin succeeds only when the regular `Authorization: Bearer ...` token is present. Static console routes remain public, and `/console/setup` remains public only for setup handoff content.

### Local-only and air-gapped modes

Mery supports explicit `local_only` / `air_gapped` policy modes. When enabled:

- No remote catalog refresh.
- No remote provider calls.
- No model downloads from network.
- Only bundled or already-local artifacts are usable.
- Network paths fail with structured errors.
- Console clearly shows that network operations are disabled.

Current enforcement evidence:

| Network path | Enforcement point | Structured failure |
|---|---|---|
| Remote catalog refresh | `CatalogRefreshService.refresh(...)` blocks before verification or `remote-catalog.json` persistence when `local_only` or `air_gapped` is set. | `network_disabled:<policy>:catalog_refresh` |
| Model/artifact downloads | `HttpArtifactSource.fetch(...)` blocks before importing `httpx`, creating target directories, or opening a connection when `local_only` or `air_gapped` is set. | `network_disabled:<policy>:model_download` |
| Remote provider calls | `SpeechSynthesisService` blocks providers marked `remote` before calling the adapter when `local_only` or `air_gapped` is set. | HTTP `503`, native code `connection.timeout`, sanitized diagnostic fields `reason=network_disabled`, `policy=<policy>`, `operation=remote_provider`, `provider_id=<id>` |

In `air_gapped` mode, guidance may describe what would need to be installed or enabled later, but runtime code must not import network clients, create remote catalog state, call provider adapters that represent remote services, or open outbound sockets for these operations.

### Remote providers

Remote providers are always opt-in. They are never enabled by default, never required for `doctor`, and never used as fallback unless the user/admin explicitly allows that policy. Remote provider usage creates audit metadata but must not store raw input text.

Current remote-provider policy evidence:

| Policy question | Current behavior |
|---|---|
| Enabled by default? | No. `RemoteProviderPolicy()` has no enabled providers and `require_enabled(provider, operation=...)` fails with `remote_provider.disabled`. |
| Fallback enabled by provider opt-in alone? | No. Provider usage and provider fallback are separate decisions; `require_fallback_allowed(provider)` fails with `remote_provider.fallback_disabled` unless the fallback policy explicitly opts in. |
| Required for `doctor`? | No. `doctor` uses local installer/backend checks and remains independent of remote-provider policy. |
| Audit metadata | Allowed remote usage emits sanitized audit metadata with provider id, operation, fallback flag, client id, and safe request metadata such as text length/locale; raw text, tokens, private paths, and audio/reference data are removed by audit redaction. |

### Text privacy

Mery must not log or persist raw input text by default. Allowed metadata includes text length, locale, voice/provider id, request id, duration/latency, error code/category, fallback status, and cancellation status.

A future raw-text debug mode, if added, must be explicit, temporary, clearly warned, auto-expiring, and have clear/export controls.

### Audit log

Audit log is separate from diagnostics history. Diagnostics explain runtime behavior; audit answers who/what did what, when, with which permission.

Initial audit events include pairing, token rotation, install confirmation, future direct-install grants, catalog/source changes, and security-sensitive configuration changes. Audit logs are local-only, bounded, sanitized, and never store raw text, tokens, reference audio, or private paths.

Current audit schema evidence:

| Field | Purpose |
|---|---|
| `schemaVersion` | Stable audit schema version, currently `v1`. |
| `eventId` | Local audit event identifier. |
| `eventType` | Stable machine-readable security event type, for example `pairing.created`, `pairing.claimed`, `token.rotated`, `install.confirmed`, `direct_install_grant.created`, `catalog.source_changed`, `security_config.changed`. |
| `occurredAt` | Event timestamp. |
| `actor` | Sanitized local actor/client identifier, never a bearer token. |
| `action` | Human-readable action string aligned with event type. |
| `outcome` | `success`, `denied`, or `failed`. |
| `metadata` | Sanitized scalar metadata only. |

Audit storage is `audit/events.json`, separate from diagnostics storage `diagnostics/events.json`. The audit store is bounded by retention days and max event count, and its redaction removes raw input text, tokens, authorization values, reference audio, binary audio, and private filesystem paths before persistence or API/export reuse.

### Direct install permissions

Direct client-triggered installs remain disabled by default. Future direct-install grants are scoped by client identity, allowed install class, short time window, and user confirmation. Grants are ephemeral by default; persistent grants require a permissions UI, revocation, audit trail, and expiry.

Current direct-install grant policy evidence:

| Boundary | Current behavior |
|---|---|
| Disabled by default | `DirectInstallGrantPolicy()` denies every request with `direct_install.disabled`. |
| Client scope | Grants match a specific `client_id`; mismatches return `direct_install.client_mismatch`. |
| Install-class scope | Grants allow explicit install classes such as `voice-pack`; disallowed classes return `direct_install.install_class_denied`. |
| Time window | Grants expire via `expires_at`; expired grants return `direct_install.expired`. |
| Revocation | Revoked grants return `direct_install.revoked`. |
| User confirmation | Grants require `user_confirmed=true`; otherwise requests return `direct_install.user_confirmation_required`. |
| Local-only / air-gapped | Direct install use is denied with `network_disabled:<policy>:direct_install` when those modes are active. |
| Audit | Grant usage metadata is sanitized and uses `direct_install_grant.created`; raw text, tokens, private paths, audio/reference data are removed before persistence. |

## Rationale

Local-first only matters if the runtime can enforce it. A named `local_only` / `air_gapped` policy makes privacy testable instead of aspirational.

Treating the console as untrusted preserves SoC and avoids privileged frontend shortcuts. Separating audit from diagnostics keeps debugging and accountability concerns clean.

## Consequences

- Security tests must treat console requests as normal browser requests.
- Network operations must check local-only policy before remote activity.
- Remote provider support must include explicit configuration and audit metadata.
- Diagnostics/export code must test redaction of raw text, tokens, audio, and private paths.
- Future permissions UI is required before persistent direct-install grants.

## Related

- [ADR-0006 — Full localhost security model](ADR-0006-security-model.md)
- [ADR-0009 — Pairing code + setup URL](ADR-0009-pairing-flow.md)
- [ADR-0010 — Full structured error taxonomy](ADR-0010-error-taxonomy.md)
- [ADR-0026 — Standalone setup boundary and client responsibilities](ADR-0026-standalone-setup-boundary.md)
- [ADR-0038 — React Console Architecture and AI-Agent Design Contract](ADR-0038-react-console-ai-agent-contract.md)
- [ADR-0040 — Governance and Voice Provenance](ADR-0040-governance-and-voice-provenance.md)
- `docs/integration/future-direct-install-permissions.md`

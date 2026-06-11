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

### Local-only and air-gapped modes

Mery supports explicit `local_only` / `air_gapped` policy modes. When enabled:

- No remote catalog refresh.
- No remote provider calls.
- No model downloads from network.
- Only bundled or already-local artifacts are usable.
- Network paths fail with structured errors.
- Console clearly shows that network operations are disabled.

### Remote providers

Remote providers are always opt-in. They are never enabled by default, never required for `doctor`, and never used as fallback unless the user/admin explicitly allows that policy. Remote provider usage creates audit metadata but must not store raw input text.

### Text privacy

Mery must not log or persist raw input text by default. Allowed metadata includes text length, locale, voice/provider id, request id, duration/latency, error code/category, fallback status, and cancellation status.

A future raw-text debug mode, if added, must be explicit, temporary, clearly warned, auto-expiring, and have clear/export controls.

### Audit log

Audit log is separate from diagnostics history. Diagnostics explain runtime behavior; audit answers who/what did what, when, with which permission.

Initial audit events include pairing, token rotation, install confirmation, future direct-install grants, catalog/source changes, and security-sensitive configuration changes. Audit logs are local-only, bounded, sanitized, and never store raw text, tokens, reference audio, or private paths.

### Direct install permissions

Direct client-triggered installs remain disabled by default. Future direct-install grants are scoped by client identity, allowed install class, short time window, and user confirmation. Grants are ephemeral by default; persistent grants require a permissions UI, revocation, audit trail, and expiry.

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

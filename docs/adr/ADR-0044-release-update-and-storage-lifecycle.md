# ADR-0044 — Release, Update, and Storage Lifecycle

**Status:** Proposed
**Date:** 2026-06-11
**Source:** Grilling session — versioning, updates, rollback, catalog, registry, and storage quota

## Context

Mery has multiple versioned surfaces: the Python package, `/v1` API, catalog schema, voice pack manifest, provider capabilities, and packaged console assets. It also manages local artifacts such as model files, catalogs, caches, diagnostics history, and future generated frontend assets.

Production readiness requires clear compatibility rules, explicit update behavior, rollback strategy, and storage cleanup policy.

## Decision

Use layered versioning and explicit user/admin-controlled updates.

### Versioning

Version layers are separate:

- App/package version — release version of Mery.
- API major path — `/v1`, changed only for breaking API changes.
- Catalog schema version — e.g. `catalog-v1`.
- Voice pack manifest version — install graph/pack format compatibility.
- Provider capability version — added only if capability metadata becomes complex.

Do not infer API/schema compatibility from app version alone.

API compatibility policy:

- Additive optional fields may stay in `/v1`.
- Existing field meaning, error envelope, and binary response semantics must not change.
- `/v2` is reserved for breaking changes.
- Contract tests must prove older clients ignore additive fields safely.

### Updates

Mery does not silently auto-update itself. App updates go through the package manager or future installer.

Catalog refresh and model/voice download require explicit user/admin action or explicit admin policy. `local_only` / `air_gapped` mode blocks network updates. Updates must validate checksums and signatures where applicable. Console/CLI should show source, size, license, version, and capability impact before install.

### Catalog and model rollback

Catalogs need version pinning and rollback to the previous valid catalog because metadata errors can affect many voices and installs.

Model artifacts initially use mark-corrupt + reinstall-same-version. Keeping previous model versions is deferred because it increases storage cost. A future admin setting may retain previous model versions for rollback.

### Storage quota and cleanup

Storage quota is advisory first, enforcement later. Doctor/Console should show models/cache/logs/diagnostics sizes, warn on thresholds, and provide cleanup for caches/logs/diagnostics. Mery must not auto-delete models or voices in active use until a safe eviction policy is accepted.

### Catalog versus model registry

The near-term system uses curated/bundled catalogs. A model registry with blobs/layers/pull/push semantics is deferred. Catalog metadata should not block a future registry: model IDs, artifact identity, checksums, and artifact source boundaries must remain stable.

## Rationale

Layered versioning prevents coupling unrelated compatibility surfaces. Explicit update actions preserve local-first trust and avoid silent network mutation.

Catalog rollback is more urgent than model rollback because catalog mistakes can corrupt user-facing visibility and install decisions broadly. Model rollback can be deferred until storage policy supports it.

## Consequences

- New schema fields must be additive or require a new major API version.
- Catalog refresh needs previous-valid pinning.
- Update flows need user/admin confirmation and structured diagnostics.
- Storage UI starts with measurement and cleanup, not automatic eviction.
- Community/model registry work remains gated behind governance and a separate registry decision.

## Related

- [ADR-0007 — Signed catalog + checksums + allowlist](ADR-0007-catalog-integrity.md)
- [ADR-0008 — Budget-aware phased packaging](ADR-0008-packaging.md)
- [ADR-0011 — Server-owned storage with platformdirs and user override](ADR-0011-storage-architecture.md)
- [ADR-0015 — Catalog model: normalized internal, flat external, artifact/voice identity](ADR-0015-catalog-model-artifact-voice-identity.md)
- [ADR-0023 — Model install and artifact source architecture](ADR-0023-model-install-and-artifact-source-architecture.md)
- [ADR-0040 — Governance and Voice Provenance](ADR-0040-governance-and-voice-provenance.md)

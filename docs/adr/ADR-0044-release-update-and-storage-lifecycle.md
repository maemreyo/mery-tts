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

Current `/v1/health` evidence exposes the additive `version_layers` object:

```json
{
  "schema_version": "v1",
  "helper_version": "0.1.0",
  "contract_version": "v1",
  "version_layers": {
    "app_version": "0.1.0",
    "api_major": "v1",
    "catalog_schema_version": "catalog-v1",
    "voice_pack_manifest_version": "voice-pack-v1",
    "provider_capability_version": "provider-capability-v1"
  }
}
```

API compatibility policy:

- Additive optional fields may stay in `/v1`.
- Existing field meaning, error envelope, and binary response semantics must not change.
- `/v2` is reserved for breaking changes.
- Contract tests must prove older clients ignore additive fields safely.
- Representative old-client fixtures validate current `/v1` payloads with unknown future fields ignored, preserving additive compatibility.

### Updates

Mery does not silently auto-update itself. App updates go through the package manager or future installer.

Catalog refresh and model/voice download require explicit user/admin action or explicit admin policy. `local_only` / `air_gapped` mode blocks network updates. Updates must validate checksums and signatures where applicable. Console/CLI should show source, size, license, version, and capability impact before install.

Current update-confirmation evidence:

- `/v1/models/install` requires `user_confirmed=true` before starting an install job; missing confirmation returns structured `409` error `update.confirmation_required` with recommended action `confirm_update`.
- The Console install action uses `window.confirm()` before calling `/v1/models/install` and includes source, size, license, version, and capability-impact copy in the prompt.
- Confirmation is additive on the `/v1` request schema; old or automated clients fail safely instead of silently mutating local model state.
- Integrity evidence is covered by catalog signature verification, checksum/size validation, failed-refresh non-mutation, and local-only/air-gapped network blocking tests.

### Catalog and model rollback

Catalogs need version pinning and rollback to the previous valid catalog because metadata errors can affect many voices and installs.

Current catalog evidence:

- `CatalogRefreshService.refresh()` writes verified remote catalogs atomically and copies the active catalog to `remote-catalog.previous.json` before replacement.
- `CatalogRefreshService.rollback_to_previous_valid()` restores the previous valid catalog through a rollback temp file and returns the restored catalog metadata.
- Failed signature validation leaves the active catalog unchanged.

Model artifacts initially use mark-corrupt + reinstall-same-version. Keeping previous model versions is deferred because it increases storage cost. A future admin setting may retain previous model versions for rollback.

Current model-artifact evidence:

- `CatalogInstaller.ensure_installed()` verifies installed artifact size/checksum before reuse.
- Corrupt installs are quarantined as `.corrupt`, reinstalled from the same catalog version, then the quarantine is removed after successful reinstall.
- State transitions are explicit: `corrupt -> installed` with action `reinstalled_same_version`; valid installs remain `installed -> installed` with action `kept_same_version`.

### Storage quota and cleanup

Storage quota is advisory first, enforcement later. Doctor/Console should show models/cache/logs/diagnostics sizes, warn on thresholds, and provide cleanup for caches/logs/diagnostics. Mery must not auto-delete models or voices in active use until a safe eviction policy is accepted.

Current storage measurement evidence:

- `/v1/storage` reports additive `breakdown` bytes for `models`, `cache`, `logs`, and `diagnostics`.
- `/v1/storage` reports an advisory object with configurable `MERY_TTS_STORAGE_WARN_BYTES`, current usage, `ok`/`warn` status, and cleanup-is-user-controlled message.
- The Console Diagnostics panel renders a Storage advisory section from `/v1/storage` as informational copy before any destructive cleanup actions.
- Empty and partial install states measure as zero for missing directories because category measurement treats absent directories as `0` bytes.

Current cleanup evidence:

- CLI `mery storage cleanup --target cache|logs|diagnostics` removes only the selected safe category and prints `models_protected=true` audit-style evidence.
- CLI `mery storage cleanup --target models` is refused and leaves active model artifacts intact.
- `/v1/storage/cleanup` accepts only `cache`, `logs`, and `diagnostics` as destructive safe targets; `models` returns structured `409` error `storage.model_cleanup_refused`.
- The Console exposes only safe cleanup buttons for cache, logs, and diagnostics; it does not expose model cleanup and displays `models_protected` after cleanup.

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

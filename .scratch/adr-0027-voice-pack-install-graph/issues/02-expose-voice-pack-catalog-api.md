# Expose VoicePack catalog API

Status: completed

## Parent

ADR-0027 — `docs/adr/ADR-0027-voice-pack-install-graph.md`

## What to build

Expose a client-safe `/v1/voice-packs` projection so Console, CLI, Zam Reader, and future clients can discover installable voice experiences.

## Acceptance criteria

- [x] `GET /v1/voice-packs` returns voice pack IDs, names, locale/use-case metadata, estimated size, runtime requirements, and install/readiness status.
- [x] Response hides raw artifact paths and unsafe provider internals.
- [x] Existing `/v1/catalog/voices` remains stable or redirects through a documented compatibility path.
- [x] Pack status reflects missing runtime, missing artifacts, installed, smoked, and failed states.

## Production-ready criteria

- [x] Contract tests cover empty catalog, bundled packs, installed packs, and missing runtime packs.
- [x] CLI can list voice packs using the same service projection.
- [x] Docs show sample response for Zam Reader and generic clients.

## Blocked by

- ADR-0027 issue 01-add-voice-pack-graph-schema

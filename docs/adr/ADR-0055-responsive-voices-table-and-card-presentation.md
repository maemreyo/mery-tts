# ADR-0055 — Responsive Voices Table and Card Presentation

**Status:** Accepted
**Date:** 2026-06-12  
**Source:** Web Console Runtime Control Plane grill — Voices UI decisions

## Context

Voices is the first substantial Console feature. It currently combines data fetching, filtering, sorting, table column definitions, install mutation, install polling, status text, and confirmation UI in one panel. The Console design contract requires table-first desktop scanning and card/stacked behavior on narrow screens.

## Decision

Keep Voices **table-first on desktop** and **card-first on mobile**, backed by a shared `VoiceViewModel` and feature hook/state layer.

The Voices feature should separate:

- data orchestration, query keys, mutation, filtering, sorting, and install status into hooks/view models;
- presentation into focused components such as toolbar, desktop table, mobile cards, install status banner, and install action;
- install job state as local to Voices v1 because the current Console client has no durable job-list source of truth.

Overview v1 must not depend on Voices' local active install job state. A future Job Center or shared install-job module may lift that state once the backend/client exposes an appropriate source.

## Rationale

The table supports high-readability scanning across voice name, engine/provider, locale, governance/risk, install state, and action. Cards improve mobile readability without duplicating business logic. Keeping install job state local avoids over-engineering while preserving a migration path.

## Consequences

**Enables:** responsive UX, smaller testable components, and future Job Center migration.

**Constrains:** no Overview “last install job” in v1; no multi-install history unless a shared durable source is added.

## Related

- [ADR-0016 — Install job lifecycle](ADR-0016-install-job-lifecycle.md)
- [ADR-0020 — Web console architecture](ADR-0020-web-console-architecture.md)
- [ADR-0052 — Web Console Runtime Control Plane](ADR-0052-web-console-runtime-control-plane.md)
- [docs/console/DESIGN.md](../console/DESIGN.md)
- Issue set: `.scratch/web-console-runtime-control-plane/`

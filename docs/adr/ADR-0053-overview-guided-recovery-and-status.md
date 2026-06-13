# ADR-0053 — Overview Guided Recovery and Status

**Status:** Accepted
**Date:** 2026-06-12  
**Source:** Web Console Runtime Control Plane grill — Overview landing decisions

## Context

The current Console opens into feature sections and requires users to infer what to do next. Local TTS users usually ask one practical question first: “Can I use Mery right now, and if not, what should I do?” A dashboard of raw numbers alone does not answer that question, while a pure wizard can hide useful status for returning users.

## Decision

Add **Overview** as the default landing section for Console v1.

Overview combines:

- a **guided recovery flow** as the primary layer;
- a compact **status summary dashboard** as supporting evidence;
- exactly one primary next action at a time, plus at most two secondary actions;
- a pure view-model decision engine that derives copy, status tiles, and actions from existing Console data.

Overview v1 uses only current capabilities:

- connection/token state;
- `/v1/health` readiness/status and usable voice count;
- `/v1/catalog/voices` voice availability where available;
- navigation to Voices, Playground, Health, or Developer.

Overview v1 must not display “last install job” or persisted smoke result because those states are currently local to Voices and Playground respectively. It may link to Playground to run speech smoke, but it must not own voice selection or synthesis logic.

## Rationale

Guided recovery is more user-centric than a telemetry-first dashboard for a local appliance. Keeping status tiles below the next action preserves operational clarity without forcing users to interpret raw health signals.

A pure view-model module makes the decision engine highly testable without DOM, backend, or browser dependencies.

## Consequences

**Enables:** deterministic unit tests for next-action selection, readable Overview components, and future extension to job center or event data when backend sources exist.

**Constrains:** Overview may not invent durable install-job or smoke-result state before there is a shared source of truth.

## Related

- [ADR-0052 — Web Console Runtime Control Plane](ADR-0052-web-console-runtime-control-plane.md)
- [ADR-0054 — Console Connection Module and Shared Query Keys](ADR-0054-console-connection-module-and-shared-query-keys.md)
- [docs/console/DESIGN.md](../console/DESIGN.md)
- Issue set: `.scratch/web-console-runtime-control-plane/`

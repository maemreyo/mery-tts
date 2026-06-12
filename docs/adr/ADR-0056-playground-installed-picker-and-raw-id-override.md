# ADR-0056 — Playground Installed Voice Picker and Raw ID Override

**Status:** Proposed  
**Date:** 2026-06-12  
**Source:** Web Console Runtime Control Plane grill — Playground voice-selection decisions

## Context

The current Playground asks users to type a raw voice model id before running speech smoke. That is flexible for developers but poor for normal users: it is easy to mistype and does not guide the user toward installed voices.

## Decision

Make the Playground default path an **installed voice picker** derived from the voice catalog.

Keep raw model id input as an **Advanced options** fallback inside Playground, collapsed by default. Do not move raw id input to Developer Mode because the action remains a Playground smoke/synthesis action, not a diagnostics-only task.

Playground must:

- use the same `MeryApiClient`/generated wrapper boundary as other features;
- choose from installed voices by default;
- validate that exactly one model id source is active before calling speech smoke;
- keep smoke mutation/result state local to Playground in v1;
- expose a clear empty state when no installed voices are available, with navigation to Voices.

## Rationale

Installed voice picker is user-centric and reduces avoidable backend errors. Keeping manual raw id behind collapsed advanced options preserves developer flexibility without making raw ids the primary UX.

## Consequences

**Enables:** safer smoke flows, fewer invalid model-id failures, better first-run guidance.

**Constrains:** Overview does not choose a voice or own smoke results; raw ids remain advanced and explicit.

## Related

- [ADR-0014 — OpenAI-compatible speech layer](ADR-0014-openai-compatible-speech-layer.md)
- [ADR-0020 — Web console architecture](ADR-0020-web-console-architecture.md)
- [ADR-0052 — Web Console Runtime Control Plane](ADR-0052-web-console-runtime-control-plane.md)
- [ADR-0055 — Responsive Voices Table and Card Presentation](ADR-0055-responsive-voices-table-and-card-presentation.md)
- Issue set: `.scratch/web-console-runtime-control-plane/`

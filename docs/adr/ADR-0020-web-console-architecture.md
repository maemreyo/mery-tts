# ADR-0020 — Web console architecture

**Status:** Proposed  
**Date:** 2026-06-05  
**Source:** Grill 05, Q47–Q55

## Context

Mery needs a local web/admin surface for catalog browsing, installs, installed voices, diagnostics, and speech smoke tests. The console must not become a second backend or require separate hosting for a local helper.

## Decision

Build a local admin console as a static SPA served by Mery at `/console`. The bundle calls same-origin `/v1` APIs. Production/local user mode does not require a frontend dev server or Node.js runtime.

Use:

```text
Vite + React + TypeScript
TanStack Query
Vitest + Testing Library + MSW
```

Avoid SSR and Next.js for the first milestone.

The web console reuses the existing API bearer token. The UI shows a local token entry screen, stores the token in memory by default, and may persist it only through an explicit “remember on this device” opt-in.

Use polling first for install jobs. WebSocket `/v1/events` is a later progressive enhancement.

The first implementation slice is Catalog + install job lifecycle:

```text
catalog table -> Install -> job polling -> installed state refresh
```

Try Speech uses blocking WAV playback first through `/v1/audio/speech` with `response_format=wav` and `stream=false`. Raw PCM streaming playback is deferred until a proper Web Audio helper exists.

Catalog UI is table-first on desktop with compact cards on narrow screens.

## Rationale

- Serving the SPA from Mery avoids CORS, separate hosting, and separate auth assumptions.
- API-driven design keeps backend/domain logic authoritative.
- TanStack Query handles server state, polling, cache invalidation, and mutations cleanly.
- Polling and WAV playback are simpler and more testable first slices than WebSocket events or raw PCM playback.
- Table-first catalog UI scales to many providers and voices.

## Consequences

**Enables:** local operational visibility, testable web flows with mocked APIs, and packaged console deployment with Mery.

**Constrains:** the first web milestone is not a marketplace, voice-cloning studio, provider tuning UI, or low-latency browser PCM player.

## Related

- ADR-0005 — Hybrid REST + WebSocket protocol
- ADR-0006 — Full localhost security model
- ADR-0014 — OpenAI-compatible speech layer
- ADR-0016 — Install job lifecycle
- `docs/grills/openai-comp/05-web-console-design.md`

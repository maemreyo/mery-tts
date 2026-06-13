# ADR-0057 — Diagnostics-Ready Health and Developer Schema Preview

**Status:** Accepted
**Date:** 2026-06-12  
**Source:** Web Console Runtime Control Plane grill — Health and Developer decisions

## Context

Health currently displays a small readiness/status summary. Developer Mode currently shows a static sanitized example. Existing backend/generated client capabilities do not yet expose a live diagnostics inspector endpoint for the React Console. The Console must not overpromise live diagnostics or leak private data.

## Decision

Keep the UI label **Health** in v1 while designing the feature as diagnostics-ready.

Health v1 should show existing health/readiness signals and recovery links without claiming full diagnostics history.

Developer remains an **Advanced** sidebar section. Developer v1 provides a clearly labeled sanitized schema preview, not a live diagnostics inspector. Copy must make the boundary explicit, e.g. “Preview of sanitized diagnostic payload shape — live diagnostics are not connected yet.”

Error states in User Mode may deep-link to Health or Developer when inspection is useful, but Developer content remains opt-in and visually distinct.

## Rationale

This preserves user trust. A static schema preview is acceptable only when it is labeled as a preview. Full diagnostics must wait for a real `/v1` contract and sanitizer tests.

## Consequences

**Enables:** diagnostics-ready structure, explicit privacy boundary, and future live inspector expansion.

**Constrains:** no fake live diagnostics, no raw headers/payload display without sanitization contract, no hidden Developer Mode coupling inside user surfaces.

## Related

- [ADR-0010 — Full structured error taxonomy](ADR-0010-error-taxonomy.md)
- [ADR-0025 — Readiness, health, smoke, and Zam Reader gating](ADR-0025-readiness-health-smoke-and-zam-reader-gating.md)
- [ADR-0041 — Operations, Observability, and Diagnostics History](ADR-0041-operations-observability-and-diagnostics-history.md)
- [ADR-0043 — Security, Privacy, and Audit](ADR-0043-security-privacy-and-audit.md)
- [ADR-0052 — Web Console Runtime Control Plane](ADR-0052-web-console-runtime-control-plane.md)
- Issue set: `.scratch/web-console-runtime-control-plane/`

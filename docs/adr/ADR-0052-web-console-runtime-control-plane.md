# ADR-0052 — Web Console Runtime Control Plane

**Status:** Accepted
**Date:** 2026-06-12  
**Source:** Web Console Runtime Control Plane grill — Overview, Connection, Voices, Playground, Health, Developer, and QA scope

## Context

The React Console already exposes a small local control surface: bearer-token session entry, voice catalog browsing, voice install polling, health polling, speech smoke, and a Developer Mode schema example. The next Console phase needs to become more production-ready without expanding beyond current runtime capabilities or duplicating backend logic.

The product framing is the main decision. If the Console is treated as only a voice manager, health, smoke, diagnostics, and future activity/history surfaces become awkward secondary pages. If it is treated as a runtime control plane, the Console can guide users through local readiness and recovery while keeping Developer Mode explicitly opt-in.

## Decision

Frame the Web Console as a **local runtime control plane** for Mery, not as a voice-store or voice-manager-only product.

The Console must:

- consume same-origin `/v1` through generated-client wrappers and feature hooks;
- avoid duplicating synthesis, install, readiness, diagnostics, auth, fallback, streaming, or storage policy;
- use **User Mode** for readiness, connection, voice availability, install recovery, and speech smoke;
- keep **Developer Mode** as an Advanced section with explicit opt-in diagnostics and schema/detail surfaces;
- prefer guided recovery and next actions over raw telemetry-first dashboards;
- remain standalone: build-time web tooling is allowed, runtime users must not need Node.js.

## Rationale

A runtime control plane matches Mery's domain better than a voice catalog alone. Mery owns local runtime readiness, voice/model lifecycle, synthesis smoke, diagnostics, packaging, and privacy boundaries. The Console should expose those capabilities through clear recovery paths without becoming a second backend.

This framing keeps the UI scalable: Overview, Connection, Voices, Playground, Health, and Developer can evolve as independent features while sharing the same control-plane contract.

## Consequences

**Enables:** a coherent IA for Overview, Voices, Playground, Health, and Developer; user-centric first-run and recovery flows; modular feature slices that remain tied to backend `/v1` contracts.

**Constrains:** no Console-only runtime behavior, no marketplace/storefront scope, no cloud account model, no provider tuning UI, no live diagnostics unless `/v1` exposes a compatible sanitized contract.

## Related

- [ADR-0020 — Web console architecture](ADR-0020-web-console-architecture.md)
- [ADR-0037 — Core Runtime Contract Before Console Expansion](ADR-0037-core-runtime-contract.md)
- [ADR-0038 — React Console Architecture and AI-Agent Design Contract](ADR-0038-react-console-ai-agent-contract.md)
- [ADR-0041 — Operations, Observability, and Diagnostics History](ADR-0041-operations-observability-and-diagnostics-history.md)
- [docs/console/DESIGN.md](../console/DESIGN.md)
- Issue set: `.scratch/web-console-runtime-control-plane/`

# ADR-0054 — Console Connection Module and Shared Query Keys

**Status:** Proposed  
**Date:** 2026-06-12  
**Source:** Web Console Runtime Control Plane grill — connection and cache decisions

## Context

The current AppShell owns bearer-token session state and passes the token into panels. Health, Sidebar, Voices, and future Overview data all need the same runtime connection and cache semantics. Leaving connection form state inside AppShell makes the shell harder to read, harder to test, and harder to evolve toward pairing/setup flows.

## Decision

Create a Console **Connection** feature/module for product-facing connection UX and session orchestration.

Use the product term **Connection** rather than **Session** for the feature name. The user-facing flow is “Connect to local Mery,” while bearer-token storage remains an implementation primitive.

Connection v1:

- moves primary auth/token entry into an Overview Connection card;
- leaves TopBar as compact connection status plus logout;
- does not expose server URL/base path UI;
- keeps same-origin `/v1` as the runtime API boundary;
- may reuse low-level storage primitives from `shared/auth` or move them behind the Connection module;
- shares React Query cache by standardizing keys for health and voices, e.g. the same key shapes consumed by Overview, Health, Voices, and Sidebar.

## Rationale

Connection is a better product domain than raw auth/session because future pairing, setup URL handoff, and reachability states all belong to “connection to local Mery.” Not exposing base URL in v1 preserves standalone same-origin packaging and avoids unnecessary security/test complexity.

Shared query keys prevent duplicate polling, stale dashboard data, and inconsistent status between Overview, Health, Sidebar, and Voices.

## Consequences

**Enables:** AppShell as composition root, reusable connection state, consistent React Query caching, and easier future pairing/setup expansion.

**Constrains:** Console v1 stays same-origin only; no user-configurable remote server URL, multi-server selector, or cloud account abstraction.

## Related

- [ADR-0006 — Full localhost security model](ADR-0006-security-model.md)
- [ADR-0009 — Pairing code + setup URL](ADR-0009-pairing-flow.md)
- [ADR-0020 — Web console architecture](ADR-0020-web-console-architecture.md)
- [ADR-0052 — Web Console Runtime Control Plane](ADR-0052-web-console-runtime-control-plane.md)
- Issue set: `.scratch/web-console-runtime-control-plane/`

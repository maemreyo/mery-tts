# ADR-0038 — React Console Architecture and AI-Agent Design Contract

**Status:** Proposed
**Date:** 2026-06-11
**Source:** Grilling session — production-ready React console and DESIGN.md contract

## Context

The current Mery Console is a small packaged vanilla JavaScript SPA served from `src/mery_tts/console`. It proves the local-console concept: same-origin `/v1` calls, token entry, catalog browsing, install polling, blocking WAV speech playback, diagnostics, and static Python package assets served by FastAPI.

The next console phase needs to become more production-ready while preserving Mery's core constraints:

- Standalone local runtime: users must not need Node.js at runtime.
- Core-first SoC: the console consumes `/v1`; it does not reimplement backend logic.
- User-centric UX: first-run setup should guide normal users to first audio and recovery.
- Developer experience: developers should see API contracts, diagnostics, streaming metadata, headers, and examples without reading source code.
- AI-agent safety: future agents need a single design/engineering contract that prevents frontend drift, dependency sprawl, duplicated runtime logic, inaccessible UI, and untested changes.

External research found two useful DESIGN.md patterns:

1. Google Labs `design.md` style for visual tokens, component language, and AI-assisted UI consistency.
2. Google-style engineering design documents for goals/non-goals, interfaces, alternatives, guardrails, testing, rollout, and observability.

Mery Console needs both: visual/product design guidance and engineering boundaries.

## Decision

Build the next Mery Console as a **Vite + React + TypeScript static SPA** with a dedicated AI-agent contract in `docs/console/DESIGN.md` and a short index in `docs/console/README.md`.

The console source lives in `web/console/`. Built static assets are committed into `src/mery_tts/console/` and served by FastAPI through the existing `/console`, `/console/assets/*`, `/console/setup`, and SPA fallback routes. Build-time Node.js is allowed; runtime Node.js is not.

### Stack

The target frontend stack is:

- Vite + React + TypeScript.
- pnpm with committed lockfile.
- TanStack Router for type-safe routes and URL/search state.
- TanStack Query for server state and polling.
- TanStack Table for voice/catalog/job tables.
- shadcn-style owned components built on Radix primitives and Tailwind.
- React Hook Form + Zod for UI/form validation.
- Generated OpenAPI TypeScript client committed under `web/console/src/api/generated/`.
- Feature API wrappers around generated client code; components do not call raw `fetch` or generated endpoints directly.
- Recharts for normal dashboard charts; uPlot only when high-volume time-series makes SVG unsuitable.
- Zustand only for small UI/session preferences; server state stays in TanStack Query.
- i18n-ready from day one, English-only initially, using semantic namespaced keys and no hardcoded user-facing strings.

### Architecture

Use feature-sliced architecture:

- `src/features/<feature>/` for Setup, Voices, Playground, Health, Developer.
- `src/shared/` for UI primitives, API client infrastructure, i18n, config, auth/session helpers, testing helpers, and design tokens.
- `src/api/generated/` is quarantined generated code.

Import boundaries are enforced with TypeScript aliases and dependency-cruiser:

- Features may import shared modules.
- Shared modules must not import features.
- UI components must not import generated API clients directly.
- Generated API code must not import app code.
- Tests may import test utilities.

### UX and information architecture

The console has two modes:

- **User Mode** by default: setup, readiness, voice install, speech smoke, and actionable recovery.
- **Developer Mode** opt-in: raw diagnostics, response headers, API payloads, schemas, streaming metadata, and integration examples.

Primary sections are:

1. Setup — guided first-run flow.
2. Voices — catalog, installed voices, install jobs.
3. Playground — OpenAI-compatible speech and later streaming inspection.
4. Health — readiness, diagnostics, smoke status.
5. Developer — API examples, headers, schemas, raw payloads, debug metadata.

First-run uses a wizard flow; returning users land on a dashboard. The app is desktop-first but mobile-usable: critical setup, voice install, speech test, and health flows must work at small widths.

### Migration contract

Migration from the current vanilla console must preserve:

- `/console`, `/console/setup`, `/console/assets/*`, and SPA fallback behavior.
- Same-origin `/v1` API calls; no hardcoded localhost URLs.
- Public `/console/setup` with server-side validation of setup intents.
- Bearer token required for `/v1` data/actions.
- Memory-only token storage by default; optional explicit localStorage persistence.
- Packaged static assets available through `importlib.resources`.
- No Node.js runtime requirement for end users.
- Existing catalog/install/speech/diagnostics behavior until replaced by tested React equivalents.

### Quality gates

Console development must include these gates from the first slice:

- Biome formatting/linting.
- TypeScript `tsc --noEmit`.
- Vitest + React Testing Library for unit/component tests.
- MSW for API mocking.
- Playwright browser smoke against the packaged `/console` route.
- `@axe-core/playwright` for automated accessibility checks on key flows.
- dependency-cruiser for architecture boundaries.
- knip for unused dependencies/exports.
- Build freshness check verifying `web/console` output matches committed `src/mery_tts/console` assets.
- Python package-resource test verifying console assets are included in the Python package.

Root commands should expose focused console checks and eventually include them in the full project check.

## Rationale

A modern frontend stack is justified because the console is becoming a real local control plane and developer dashboard. Vanilla JavaScript is no longer the right long-term tool for typed API contracts, modular feature slices, tables, forms, i18n, accessibility checks, and browser E2E testing.

The SPA/static-asset constraint preserves Mery's standalone Python-first distribution model. Users get a local web console without installing Node.js. Contributors get modern DevExp through build-time tooling.

A `docs/console/DESIGN.md` contract gives AI agents an explicit source of truth for UI, architecture, boundaries, tests, i18n, accessibility, dependency governance, and migration invariants. This avoids repeated rediscovery and reduces the risk of AI-generated frontend sprawl.

## Consequences

- Console work starts with documentation and gates, not ad hoc component work.
- New frontend dependencies require justification against the stack and no-overlap rule.
- Generated API clients and built assets are committed for readability and standalone reliability, with CI freshness checks preventing drift.
- UI components remain user-centric and accessible while Developer Mode preserves deep diagnostics and integration DevExp.
- The console remains independent of any single client such as Zam Reader; Zam Reader can be a reference integration but not the product lock.
- The React migration is incremental: first tracer bullet is app shell, token handling, Voices catalog/install lifecycle, generated client, packaged build, and tests.

## Related

- [ADR-0001 — Product / ownership boundary](ADR-0001-product-boundary.md)
- [ADR-0005 — Hybrid REST + WebSocket protocol](ADR-0005-api-protocol.md)
- [ADR-0006 — Full localhost security model](ADR-0006-security-model.md)
- [ADR-0008 — Budget-aware phased packaging](ADR-0008-packaging.md)
- [ADR-0014 — OpenAI-compatible speech layer](ADR-0014-openai-compatible-speech-layer.md)
- [ADR-0020 — Web console architecture](ADR-0020-web-console-architecture.md)
- [ADR-0026 — Standalone setup boundary and client responsibilities](ADR-0026-standalone-setup-boundary.md)
- [ADR-0037 — Core Runtime Contract Before Console Expansion](ADR-0037-core-runtime-contract.md)

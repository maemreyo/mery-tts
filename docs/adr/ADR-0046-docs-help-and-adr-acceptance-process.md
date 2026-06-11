# ADR-0046 — Docs, Help, and ADR Acceptance Process

**Status:** Proposed
**Date:** 2026-06-11
**Source:** Grilling session — local help, branch Definition of Done, and ADR status rules

## Context

Mery uses ADRs, local markdown issues, integration docs, and agent-facing skills to keep design decisions explicit. As the roadmap grows, many ADRs remain Proposed while implementation issues exist in `.scratch`. Agents and contributors need a clear distinction between binding decisions, planned decisions, deferred work, local recovery help, and production-ready Definition of Done.

Mery is offline-first, so recovery help must not require internet access.

## Decision

Define local help packaging, branch Definition of Done, and ADR acceptance rules.

### Local help

Mery packages a small set of local help topics with the app for recovery paths. Full docs may remain in the repo or hosted docs, but critical recovery must work offline.

Local help topics include:

- install/setup
- pairing/token
- missing optional dependency
- model corrupt/reinstall
- catalog invalid/signature/checksum
- `local_only` / `air_gapped`
- diagnostics export
- unsupported format/locale
- provider unavailable

Important errors should reference a `help_topic` or `docs_url`. Console should prefer local help and use online docs only as an optional supplement.

### Branch Definition of Done

Every production branch must satisfy a common Definition of Done:

- ADR/contract updated when architecture or API changes.
- Fake-engine deterministic tests exist where runtime behavior changes.
- API contract tests exist when `/v1` changes.
- CLI or Console real-surface proof exists for user-facing behavior.
- Diagnostics/error sanitization tests exist when errors or logs change.
- No raw input text, token, reference audio, or private path logging is introduced.
- Docs/help are updated when the behavior is user-facing.
- Optional real-engine smoke is added when touching real engine paths.
- UI branches include Vitest/RTL/MSW, Playwright, and accessibility checks.

### ADR status rules

ADR statuses have explicit meaning:

- **Proposed** — design exists but still needs review/grill, issue set, or conflict resolution.
- **Accepted** — decision is binding: grill/review complete, blocking open questions resolved, issue set exists, related docs linked, and no conflict with earlier ADRs.
- **Superseded** — replaced by a later ADR.
- **Deprecated** — no longer recommended, but not directly replaced.

Agents should treat Accepted ADRs as binding law. Proposed ADRs are plans that must be checked before implementation.

### Issue tracker linkage

Each new major ADR should have a matching `.scratch/<adr-slug>/INDEX.md` and issue files. Issues are dependency-ordered and independently grabbable where possible.

## Rationale

Local help makes Mery recoverable offline. A shared branch Definition of Done prevents partially working features from being called production-ready. Explicit ADR acceptance rules prevent agents from treating every Proposed idea as binding architecture.

## Consequences

- Existing Proposed ADRs may need a review pass before being promoted to Accepted.
- Future implementation work should reference both ADR and local issue path.
- Error taxonomy should include help topics for user-actionable errors.
- Console and CLI should expose local recovery guidance consistently.

## Related

- [ADR-0001 — Product / ownership boundary](ADR-0001-product-boundary.md)
- [ADR-0008 — Budget-aware phased packaging](ADR-0008-packaging.md)
- [ADR-0010 — Full structured error taxonomy](ADR-0010-error-taxonomy.md)
- [ADR-0038 — React Console Architecture and AI-Agent Design Contract](ADR-0038-react-console-ai-agent-contract.md)
- `docs/agents/issue-tracker.md`
- `docs/agents/domain.md`

# Architecture Decision Records

All major architectural decisions for `zam-local-tts-helper` are recorded here.
Each ADR captures the context, the decision made, the rationale, and the
consequences. Once accepted, an ADR is immutable; superseded ADRs are marked as such.

These ADRs distill the 27 design decisions from
[`reports/local-tts-helper-design-decisions.md`](../reports/local-tts-helper-design-decisions.md).

---

## Status index

| ADR | Title | Status |
|---|---|---|
| [ADR-0001](ADR-0001-product-boundary.md) | Product / ownership boundary | ✅ Accepted |
| [ADR-0002](ADR-0002-helper-shape.md) | Helper shape: CLI + daemon hybrid | ✅ Accepted |
| [ADR-0003](ADR-0003-python-runtime.md) | Python-first runtime | ✅ Accepted |
| [ADR-0004](ADR-0004-engine-strategy.md) | Dual-engine from day one | ✅ Accepted |
| [ADR-0005](ADR-0005-api-protocol.md) | Hybrid REST + WebSocket protocol | ✅ Accepted |
| [ADR-0006](ADR-0006-security-model.md) | Full localhost security model | ✅ Accepted |
| [ADR-0007](ADR-0007-catalog-integrity.md) | Signed catalog + checksums + allowlist | ✅ Accepted |
| [ADR-0008](ADR-0008-packaging.md) | Budget-aware phased packaging | ✅ Accepted |
| [ADR-0009](ADR-0009-pairing-flow.md) | Pairing code + setup URL | ✅ Accepted |
| [ADR-0010](ADR-0010-error-taxonomy.md) | Full structured error taxonomy | ✅ Accepted |
| [ADR-0011](ADR-0011-storage-architecture.md) | Helper-owned storage with platformdirs and user override | ✅ Accepted |

---

## Format

Each ADR follows this template:

```markdown
# ADR-NNNN — Title

**Status:** Accepted | Proposed | Deprecated | Superseded by ADR-XXXX
**Date:** YYYY-MM-DD
**Deciders:** (list of people/roles who signed off)

## Context
What situation or problem prompted this decision?

## Decision
What was decided?

## Rationale
Why this option over the alternatives?

## Consequences
What does this decision enable? What does it constrain?

## Related
Links to related ADRs, design docs, or readiness contract sections.
```

---

## Guidance for new ADRs

- Write a new ADR whenever a major technical decision is made that would be
  costly to reverse or that future contributors would wonder about.
- ADR numbers are sequential. Never renumber existing ADRs.
- A decision that replaces an earlier one creates a new ADR and marks the old
  one as `Superseded by ADR-XXXX`.
- Keep ADRs short and to the point. The design-decisions report is where
  exhaustive rationale lives; ADRs are the portable, versioned record.

# ADR status rules

This document defines how agents and contributors interpret ADR status labels.

## Status semantics

- Proposed means needs review/grill/issue set before implementation. Treat it as a plan to validate, not binding architecture.
- Accepted means binding after review is complete, open questions resolved, issue set exists, related docs linked, and no conflict with earlier ADRs.
- Superseded means replaced by a later ADR. Follow the replacement ADR and preserve the superseded record for history.
- Deprecated means no longer recommended, but not directly replaced. Do not use it for new work unless a newer ADR explicitly revives it.

## Agent behavior

Accepted ADRs are binding law. Agents must follow them unless the user explicitly asks to create a new ADR that changes the decision.

Proposed ADRs are plans to check. Before implementing from a Proposed ADR, agents must verify whether the issue set exists, whether open questions are resolved, and whether the plan conflicts with Accepted ADRs.

## Promotion checklist

Promote an ADR to Accepted only when:

- review/grill is complete
- open questions resolved
- issue set exists
- related docs linked
- no conflict with earlier ADRs
- implementation evidence or planned slices are clear enough for independent work

Use Superseded when a later ADR replaces the decision. Use Deprecated when the decision is no longer recommended but has no direct replacement.

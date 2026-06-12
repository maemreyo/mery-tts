# Provider admission policy

Status: ADR-0049 contract

Mery does not add post-P1 providers by popularity or demo quality alone. A provider can become first-class only after maintainers complete this evidence package and the admission helper in `mery_tts.providers.taxonomy` projects it to User Mode visibility.

## Admission order

1. Complete a provider scorecard before implementation begins.
2. Classify the provider into a product tier.
3. Record pass/fail/unknown for every fit gate.
4. Run the pragmatic quality/resource golden suite.
5. Pass package-install provider e2e before default catalog or guided install exposure.
6. Record sanitized support-bundle evidence.
7. Update docs/help and Definition of Done evidence.
8. Keep Tier C providers blocked until a separate governance ADR/issues are accepted.

User demand ranks candidates only after local-fit, appliance-fit, quality-fit, and modern-fit are passed.

## Provider scorecard template

Copy this section into `docs/reports/roadmap-research/providers/<provider-id>.md` before opening provider implementation issues.

```markdown
# <Provider name> scorecard

Status: proposed | blocked | accepted | experimental-only
Related ADR: docs/adr/ADR-0049-local-modern-provider-admission-policy.md

## Summary

- Provider ID:
- Upstream project:
- Intended tier: Tier A | Tier B | Tier C | Tier D
- Intended user value:
- Recommended decision: accept | reject | defer | experimental-only

## Fit gates

| Gate | Status | Evidence | Blockers |
|---|---|---|---|
| local-fit | pass/fail/unknown | Local/offline runtime, artifacts, dependency path, hardware story, no hidden mandatory cloud dependency | |
| appliance-fit | pass/fail/unknown | Guided install/delete/diagnose/recover behavior, catalog/install/job/readiness compatibility | |
| quality-fit | pass/fail/unknown | Golden suite artifacts, latency, memory, artifact size, first-audio time, locale honesty, failure recovery | |
| modern-fit | pass/fail/unknown | Maintenance, license/provenance, stable adapter API/CLI, capability metadata, no brittle legacy hacks | |

## Required review areas

- License/provenance:
- Model size and storage impact:
- Hardware/resource envelope:
- Install complexity:
- API/CLI stability:
- Testability:
- UX risk:
- Privacy/security risk:
- Acceptance blockers:

## Golden suite evidence

- Prompt set version:
- Audio artifacts location:
- Latency and first-audio time:
- Memory/resource notes:
- Subjective maintainer notes:
- Acceptance blockers vs advisory notes:

## Package-install provider e2e

- Fresh package/tool-install environment:
- Runtime dependency detection:
- Model install lifecycle:
- Real synthesis proof:
- Installed status proof:
- Delete cleanup proof:
- Sanitized support bundle:

## Visibility decision

- Catalog visibility: User Mode | Developer Mode | Hidden
- Required badges:
- User Mode proof:
- Developer Mode/docs warning proof:

## Tier C governance review

If the provider uses voice cloning, reference audio, dialogue, multi-speaker, emotional, or other misuse-sensitive behavior, stop normal admission here and open a separate governance ADR/issues covering consent UX, provenance, reference-audio privacy, misuse controls, storage/audit policy, UI warnings, licensing clarity, and explicit opt-in.
```

## Product tiers

- **Tier A — Appliance baseline:** CPU-friendly, reliable, simple install, suitable for long-form reading and basic local assistant use.
- **Tier B — Modern high-quality local:** higher quality local providers that still pass local-fit, appliance-fit, quality-fit, and modern-fit. P2 targets this tier.
- **Tier C — Specialist/governance-gated:** voice cloning, reference audio, dialogue, multi-speaker, emotional, or other misuse-sensitive providers. These require separate governance before user exposure.
- **Tier D — Research/unsupported:** maintainer research only; not default catalog or install wizard content.

## Visibility policy

| Condition | Catalog visibility | Wizard exposure | Required badges |
|---|---|---|---|
| Tier A/B, all gates pass, scorecard complete, package e2e pass, support bundle evidence recorded | User Mode | Allowed | none |
| Experimental candidate | Developer Mode/docs only | Blocked | `experimental`, `not appliance-ready`, `manual setup`, `not supported by wizard`, `package e2e may fail` |
| Tier C candidate | Developer Mode/docs only until governance accepted | Blocked | `not appliance-ready`, `not supported by wizard` |
| Tier D candidate | Developer Mode/docs only or hidden | Blocked | `not appliance-ready`, `not supported by wizard` |
| Incomplete scorecard/evidence | Hidden | Blocked | `not appliance-ready`, `package e2e may fail` |

## P2 release checklist

Before a provider becomes first-class P2 catalog/install wizard support, record:

- completed provider scorecard;
- tier classification and catalog visibility decision;
- local-fit, appliance-fit, quality-fit, and modern-fit pass evidence;
- pragmatic quality/resource golden suite evidence;
- package-install provider e2e pass;
- support bundle evidence for success and failure paths;
- license/provenance review;
- privacy/security review;
- hardware/resource review;
- docs/help updates;
- User Mode and Developer Mode visibility proof;
- Tier C governance ADR/issues if the provider is misuse-sensitive;
- branch Definition of Done evidence.

## Related

- [ADR-0049 — Local-Modern Provider Admission Policy](../adr/ADR-0049-local-modern-provider-admission-policy.md)
- [ADR-0018 — Provider Rollout Strategy](../adr/ADR-0018-provider-rollout-strategy.md)
- [ADR-0019 — Provider Adapter Taxonomy](../adr/ADR-0019-provider-adapter-taxonomy.md)
- [ADR-0040 — Governance and Voice Provenance](../adr/ADR-0040-governance-and-voice-provenance.md)
- [ADR-0048 — Dependable Local TTS Appliance Milestone](../adr/ADR-0048-dependable-local-tts-appliance.md)
- [Provider adapter taxonomy](adapter-taxonomy.md)

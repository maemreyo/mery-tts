# PRD — P2 Local-Modern Provider Admission Policy

Status: ready-for-agent
Date: 2026-06-11
ADR: docs/adr/ADR-0049-local-modern-provider-admission-policy.md
Issue index: .scratch/adr-0049-local-modern-provider-admission-policy/INDEX.md

## Problem Statement

After P1 makes Mery a dependable local TTS appliance, users will want better, more modern, and more expressive voices. The dangerous path is to add providers because they sound impressive in demos while ignoring whether they work as dependable local appliance components. That would create a model zoo: confusing catalogs, broken installs, unclear licenses, GPU surprises, privacy risks, support burden, and untestable provider-specific UX.

Mery needs a provider admission policy that preserves local-first reliability while still allowing high-quality modern local providers to enter the roadmap.

## Solution

P2 provider expansion uses a local-modern provider admission policy. Provider candidates must pass fit gates, tiering, scorecards, pragmatic quality/resource evaluation, package-install e2e, and catalog visibility rules before becoming first-class.

The policy optimizes for appliance-fit local providers over raw demo quality. User demand ranks candidates only after candidates pass local-fit, appliance-fit, quality-fit, and modern-fit gates.

## User Stories

1. As a Mery user, I want new providers to install and work reliably, so that trying a better voice does not break the appliance experience.
2. As a Mery user, I want experimental providers hidden from default setup, so that I am not offered fragile options by mistake.
3. As a Mery user, I want provider labels to be honest, so that I know whether a provider is baseline, modern local, experimental, or governance-gated.
4. As a Mery user, I want provider quality claims backed by repeatable evidence, so that modern voices are not added based only on hype.
5. As a maintainer, I want a provider scorecard before implementation, so that tradeoffs are visible before code is written.
6. As a maintainer, I want provider admission to require package-install e2e, so that bundled catalog entries do not fail outside a repo checkout.
7. As a maintainer, I want provider work to reuse existing adapter/catalog/install/readiness/diagnostics boundaries, so that SoC remains clean.
8. As a maintainer, I want voice cloning and dialogue systems separated into governance work, so that privacy and consent risks are handled explicitly.
9. As an integrator, I want provider capabilities exposed consistently, so that clients can avoid unsupported voices, locales, or hardware assumptions.
10. As a developer, I want research providers documented without first-class exposure, so that exploration can continue without confusing users.

## Implementation Decisions

- Provider popularity or raw demo quality is not sufficient for first-class support.
- Provider admission starts with a documented scorecard.
- Fit gates are local-fit, appliance-fit, quality-fit, and modern-fit.
- P2 targets Tier B modern high-quality local providers only.
- Tier A remains the dependable appliance baseline.
- Tier C voice cloning, reference audio, dialogue, multi-speaker, emotional, and misuse-sensitive providers require a separate governance roadmap.
- Tier D research/unsupported providers may be documented but are not exposed in default user catalog or guided install flows.
- Bundled catalog/default install wizard exposure requires package-install provider e2e pass.
- Experimental providers are hidden from default User Mode and may appear only in Developer Mode/docs with explicit warnings.
- Provider quality evidence uses a pragmatic golden suite, not a research-heavy lab MOS process.
- Provider adapters must stay modular and consume existing runtime contracts rather than adding provider-specific UI or backend shortcuts.

## Testing Decisions

- Scorecard review is required before implementation tests are written.
- Golden suite covers short text, long-form text, punctuation, numbers, abbreviations, claimed locales, mixed text when claimed, latency, memory, artifact size, first-audio time, failure recovery, subjective maintainer notes, and audio artifact evidence.
- Package-install provider e2e covers runtime dependency detection, model install, synthesize, status, delete cleanup, and support bundle evidence.
- Normal CI should keep deterministic fake/provider tests where possible; real-provider smoke is release/admission evidence.
- Catalog visibility tests must prove experimental providers are hidden from default User Mode and not offered by the install wizard.
- Governance tests/issues are required before Tier C providers become visible to normal users.

## Out of Scope

- Selecting the actual next provider.
- Implementing a Tier B provider adapter.
- Exposing voice cloning, reference-audio, dialogue, or multi-speaker systems to normal users.
- Making experimental providers available in default catalog or install wizard.
- Building a public benchmark leaderboard.
- Replacing Mery's existing provider adapter taxonomy.

## Further Notes

This PRD is a policy gate for post-P1 provider work. It protects the dependable appliance direction while leaving room for modern high-quality local providers once they prove they fit Mery's architecture and UX.

Definition of Done review for each implementation branch must follow `docs/agents/definition-of-done.md`.

# Web Console DESIGN.md Tailwind Theme Artifact PRD

Status: ready-for-agent

## Problem

`docs/console/DESIGN.md` is the Console visual/product/engineering contract, but the runtime styling can drift when CSS tokens are maintained separately. Google Labs `@google/design.md` provides lint and export commands that can make DESIGN.md operational by generating a Tailwind v4 `@theme` artifact.

## Goal

Make DESIGN.md the canonical design-token source for Web Console styling by generating and committing a Tailwind theme artifact, verifying freshness in Console checks, and migrating existing styles to consume generated theme tokens incrementally.

## In scope

- Add `@google/design.md` as a build-time/dev-time dependency.
- Add design lint, token export, and freshness-check scripts.
- Commit a generated Tailwind v4 `@theme` artifact under `web/console/src/`.
- Import the artifact from the Console style entrypoint.
- Keep standalone runtime: packaged users do not need Node.js or the design.md CLI.
- Preserve current UI behavior while the token source changes.
- Document the generation/update path for future agents.

## Out of scope for the first slice

- Full JSX/component rewrite to Tailwind utility classes.
- Full shadcn migration.
- Generating component implementations from DESIGN.md.
- Visual redesign beyond token-source migration.
- Server/API/backend changes.

## Related ADR

- `docs/adr/ADR-0059-console-design-token-tailwind-artifact.md`

## Implementation issues

- `issues/01-designmd-dependency-and-scripts.md`
- `issues/02-tailwind-theme-artifact-and-style-import.md`
- `issues/03-token-freshness-gate-and-console-check.md`
- `issues/04-incremental-style-token-migration.md`
- `issues/05-token-migration-validation-and-visual-qa.md`

## Definition of Done review

- ADR/contract updated: yes — ADR-0059 proposed and indexed.
- fake-engine deterministic tests: N/A — no runtime engine behavior.
- API contract tests: N/A — no `/v1` contract changes.
- CLI or Console proof: required by implementation issues through design scripts, build, and browser/visual evidence.
- diagnostics/error sanitization tests: N/A unless UI snapshots are changed; privacy review remains required.
- docs/help updated: yes — this PRD and ADR-0059 define the plan.
- optional real-engine smoke: N/A.
- UI gates: required by issue 05.
- privacy gates: yes — generated artifacts must not include tokens, private paths, raw text, reference audio, or private URLs.

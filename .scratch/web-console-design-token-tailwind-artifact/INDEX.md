# Web Console DESIGN.md Tailwind Theme Artifact Issue Set

Status: ready-for-agent

## Purpose

Track the design-token migration that makes `docs/console/DESIGN.md` generate a committed Tailwind v4 theme artifact for `web/console`.

## ADR

- ADR-0059 — Console DESIGN.md Tailwind Theme Artifact

## Dependency order

1. `issues/01-designmd-dependency-and-scripts.md`
2. `issues/02-tailwind-theme-artifact-and-style-import.md`
3. `issues/03-token-freshness-gate-and-console-check.md`
4. `issues/04-incremental-style-token-migration.md`
5. `issues/05-token-migration-validation-and-visual-qa.md`

## Notes for agents

- Keep scope to design-token generation and consumption unless a later issue explicitly requests component rewrite.
- Preserve standalone runtime: Node/designmd is build-time only.
- Generated artifact should be committed and reviewed.
- If DESIGN.md changes, generated artifact freshness must be checked.
- Do not add backend endpoints or change Console product behavior while working this issue set.

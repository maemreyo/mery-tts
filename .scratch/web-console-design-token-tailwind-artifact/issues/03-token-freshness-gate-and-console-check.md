# Add design-token freshness gate to console-check

Status: ready-for-agent

## What to build

Add a deterministic freshness gate that fails when `docs/console/DESIGN.md` and the committed Tailwind theme artifact diverge, and include that gate in the Web Console check pipeline.

## Acceptance criteria

- [ ] Freshness check regenerates expected output in a temporary location or memory and compares it with the committed artifact.
- [ ] Freshness check has deterministic output and no destructive side effects.
- [ ] `console-check` runs design lint and freshness checks before build freshness.
- [ ] Failure message tells contributors exactly which command to run to update the artifact.
- [ ] Unit/script-level coverage or a documented command proves stale artifact detection works.
- [ ] Existing API/build freshness scripts remain unchanged in behavior.

## Blocked by

- `01-designmd-dependency-and-scripts.md`
- `02-tailwind-theme-artifact-and-style-import.md`

## Related

- `docs/adr/ADR-0059-console-design-token-tailwind-artifact.md`
- `docs/adr/ADR-0058-console-test-accessibility-and-visual-qa-gates.md`

## Comments

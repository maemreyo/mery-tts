# Incrementally migrate existing styles to generated Tailwind theme tokens

Status: ready-for-agent

## What to build

Move existing Console styling away from hand-maintained token definitions and toward generated Tailwind theme tokens while preserving current component behavior and visual intent.

## Acceptance criteria

- [ ] Old root token definitions are removed or reduced to a clearly documented compatibility alias layer.
- [ ] Components and CSS consume generated theme variables or Tailwind theme utilities where safe.
- [ ] Complex Radix component styling is not rewritten into fragile utility-only code unless tests and visual QA cover it.
- [ ] Migration is incremental and keeps high-readability CSS/JSX boundaries.
- [ ] No UI feature behavior changes are bundled into the token migration.
- [ ] Lint, typecheck, component tests, and build pass after migration.

## Blocked by

- `02-tailwind-theme-artifact-and-style-import.md`
- `03-token-freshness-gate-and-console-check.md`

## Related

- `docs/adr/ADR-0059-console-design-token-tailwind-artifact.md`
- `docs/console/DESIGN.md`

## Comments

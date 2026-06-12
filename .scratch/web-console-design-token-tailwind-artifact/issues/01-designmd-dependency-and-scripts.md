# Add design.md dependency and generation scripts

Status: ready-for-agent

## What to build

Add `@google/design.md` to the Web Console build-time/dev-time toolchain and expose scripts for linting and exporting `docs/console/DESIGN.md` without changing runtime behavior.

## Acceptance criteria

- [ ] `@google/design.md` is added as a devDependency in `web/console/package.json` and lockfile changes are committed.
- [ ] A script lints `docs/console/DESIGN.md` using the design.md CLI or documented alias.
- [ ] A script exports DESIGN.md tokens to Tailwind v4 `@theme` format.
- [ ] Script paths work from `web/console` regardless of current shell path assumptions.
- [ ] Failure output is clear when DESIGN.md is invalid or the CLI is unavailable.
- [ ] Runtime package users do not need Node.js or `@google/design.md`.

## Blocked by

None - can start immediately.

## Related

- `docs/adr/ADR-0059-console-design-token-tailwind-artifact.md`
- `docs/console/DESIGN.md`

## Comments

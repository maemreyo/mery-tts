# Dependency cleanup — remove unused runtime packages

Status: ready-for-agent

## What to build

Two runtime dependencies ship in `package.json` but have no imports in the Console source:

- `@tanstack/react-router` — TanStack Router was removed from `main.tsx` and all feature code
  in a previous refactor to fix the post-render event loop freeze. The package remains declared
  as a dependency.
- `@radix-ui/react-tabs` — `SectionTabs.tsx` was deleted in the same refactor. The package
  remains declared as a dependency.

Both packages are Vite tree-shaken out of the production bundle (because they have no
import sites), but they still bloat `node_modules`, pollute the lockfile, and may trigger false
positives or confusion in `pnpm unused` (knip) output.

## Acceptance criteria

- [ ] `@tanstack/react-router` is removed from `package.json` `dependencies`.
- [ ] `@radix-ui/react-tabs` is removed from `package.json` `dependencies`.
- [ ] `pnpm-lock.yaml` is updated (`pnpm install` run after removal).
- [ ] `pnpm typecheck` passes — no TypeScript errors from missing packages.
- [ ] `pnpm build` passes and bundle hash is different (smaller or equal, never larger).
- [ ] `pnpm unused` (knip) no longer flags these two packages as unused.
- [ ] No source file in `src/` imports from `@tanstack/react-router` or `@radix-ui/react-tabs`
      after cleanup.

## Blocked by

None — can start immediately.

## Related

- `issues/01-runtime-control-plane-api-wrapper-and-freshness.md` (boundary enforcement will
  confirm no hidden router imports survive)

## Comments

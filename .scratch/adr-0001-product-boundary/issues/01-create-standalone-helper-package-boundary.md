# Create standalone helper package boundary

Status: ready-for-agent

## Parent

ADR-0001 — `docs/adr/ADR-0001-product-boundary.md`

## What to build

Create the initial standalone helper package shape so runtime code can live independently from Zam Reader, with a minimal importable Python package, package metadata, typed marker, and documentation that identifies `/v1` as the only integration boundary.

## Acceptance criteria

- [ ] The repository has a Python `src` package for the helper with a minimal public surface and inline type marker.
- [ ] Package metadata identifies the helper as independently installable/testable and does not reference importing Zam Reader code.
- [ ] A smoke test proves the helper package imports without requiring Zam Reader, browser APIs, engines, or model files.
- [ ] README or developer docs keep the boundary rule visible: Zam Reader talks through `/v1`, not Python imports.

## Blocked by

None - can start immediately

## Comments

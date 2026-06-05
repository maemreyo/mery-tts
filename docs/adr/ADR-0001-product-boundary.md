# ADR-0001 — Product / ownership boundary

**Status:** Accepted  
**Date:** 2026-06-05  
**Source:** Design Decision 1, 22

## Context

Zam Reader needs higher-quality, locally managed TTS. The question is whether the
extension should own the TTS runtime directly, or delegate to a separate companion
helper app.

## Decision

Use an **extension-managed companion helper** in a **separate repository**
(`zam-local-tts-helper`). Zam Reader integrates only through a versioned `/v1`
bridge contract.

## Rationale

- Browser extensions must not directly install native executables; store reviewers
  will reject extensions that do.
- A companion helper can have its own Python runtime, CI, packaging, and release
  lifecycle without polluting the WXT/TypeScript extension repo.
- The boundary is the cleanest possible SoC: the helper owns all native concerns;
  the extension owns all UI/UX concerns.
- A separate repo prevents Python packaging concerns from leaking into the strict
  `depcruise`-enforced TypeScript architecture of Zam Reader.

## Consequences

**Enables:**
- Helper is independently testable, shippable, and versionable.
- Zam Reader CI stays fast (uses a fake helper stub).
- Other future clients could use the helper without any Zam Reader dependency.

**Constrains:**
- Every API change requires coordinated versioning (contract version, not package version).
- Zam Reader must implement a fake helper for its own CI.
- Two repos to maintain.

**Hard rules:**
- Zam Reader never imports Python helper code.
- Zam Reader never sends raw filesystem paths to the helper.
- Model IDs only — no raw URLs from the browser client.

## Related

- ADR-0005 (API protocol versioning)
- `docs/integration/zam-reader-readiness-contract.md`
- `docs/zam-reader-context.md`

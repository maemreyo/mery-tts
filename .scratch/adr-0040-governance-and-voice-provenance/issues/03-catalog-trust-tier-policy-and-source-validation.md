# Catalog trust tier policy and source validation

Status: needs-triage

## Parent

ADR-0040 — `docs/adr/ADR-0040-governance-and-voice-provenance.md`

## Type

AFK

## What to build

Define bundled/curated, trusted remote, and community catalog trust tiers and validate source handling.

## Acceptance criteria

- [ ] Docs define trust tiers and required metadata.
- [ ] Arbitrary remote catalogs are not silently treated as trusted.
- [ ] Current behavior remains bundled/curated-first.
- [ ] Trust tier is visible in diagnostics or catalog summaries.

## Evidence required

- [ ] Policy doc/schema excerpt.
- [ ] Static or unit tests for source validation.
- [ ] Diagnostics/catalog summary test.

## Blocked by

- 01

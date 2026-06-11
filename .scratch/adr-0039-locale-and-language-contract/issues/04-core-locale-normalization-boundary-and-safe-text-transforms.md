# Core locale normalization boundary and safe text transforms

Status: needs-triage

## Parent

ADR-0039 — `docs/adr/ADR-0039-locale-and-language-contract.md`

## Type

AFK

## What to build

Define the core preprocessing boundary for locale-aware Unicode, punctuation, segmentation, and safe transformations before provider-specific hooks.

## Acceptance criteria

- [ ] Core preprocessing handles Unicode normalization and punctuation normalization deterministically.
- [ ] Sentence segmentation and max-length handling are locale-aware.
- [ ] Provider phoneme/G2P hooks still run after core normalization.
- [ ] Default diagnostics do not store raw or normalized text.

## Evidence required

- [ ] Core preprocessing unit tests.
- [ ] Provider adapter boundary tests with fake engine.
- [ ] Sanitization test for normalization diagnostics.

## Blocked by

- 03

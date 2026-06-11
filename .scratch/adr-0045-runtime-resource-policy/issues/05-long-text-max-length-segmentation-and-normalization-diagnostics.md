# Long text max length segmentation and normalization diagnostics

Status: needs-triage

## Parent

ADR-0045 — `docs/adr/ADR-0045-runtime-resource-policy.md`

## Type

AFK

## What to build

Enforce max length, locale-aware segmentation, structured long-input errors, and sanitized normalization diagnostics.

## Acceptance criteria

- [ ] Core enforces max text length.
- [ ] Locale-aware segmentation splits long input safely where supported.
- [ ] Unsupported long input returns structured errors.
- [ ] Diagnostics include locale, normalizer version, categories, warnings, and length metadata without raw text.

## Evidence required

- [ ] Max-length tests.
- [ ] Segmentation tests.
- [ ] Diagnostic redaction tests.
- [ ] Progress/cancellation tests where segmented synthesis exists.

## Blocked by

None - can start immediately

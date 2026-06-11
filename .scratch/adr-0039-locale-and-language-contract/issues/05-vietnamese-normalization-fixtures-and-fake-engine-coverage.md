# Vietnamese normalization fixtures and fake-engine coverage

Status: needs-triage

## Parent

ADR-0039 — `docs/adr/ADR-0039-locale-and-language-contract.md`

## Type

AFK

## What to build

Add Vietnamese-focused fixtures for diacritics, numbers, abbreviations, mixed English/Vietnamese, long sentences, and malformed input.

## Acceptance criteria

- [ ] Fixtures cover diacritics, numbers, abbreviations, mixed EN/VI, long sentences, and malformed input.
- [ ] Fake-engine tests prove routing and normalization contracts without real model packages.
- [ ] Warnings are structured and sanitized.
- [ ] Long input behavior aligns with runtime resource limits.

## Evidence required

- [ ] Fixture files for each Vietnamese case category.
- [ ] Fake-engine test run.
- [ ] Diagnostics redaction evidence.

## Blocked by

- 04

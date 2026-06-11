# Voice and catalog BCP-47 locale metadata schema

Status: ready

## Parent

ADR-0039 — `docs/adr/ADR-0039-locale-and-language-contract.md`

## Type

AFK

## What to build

Add additive BCP-47 locale metadata to voice and catalog projections so clients can discover language support without parsing names or engine IDs. The change introduces `supported_locales` as an additive array field on voice descriptors and catalog entries, validated against BCP-47 format and normalized before storage.

Behavioral contract: Each voice/catalog entry may expose one or more locale tags (`vi-VN`, `en-US`, `en-GB`). Clients read `supported_locales` to filter voices or warn users about locale mismatches. Absent or unrecognized locales do not break consumption.

## Acceptance criteria

- [ ] Voice descriptor schema exposes additive `supported_locales` array field.
- [ ] Catalog projection schema exposes additive `supported_locales` on category entries.
- [ ] Valid `vi-VN`, `en-US`, and `en-GB` tags are accepted and normalized.
- [ ] Malformed tags are rejected at schema boundaries with structured errors.
- [ ] Backward-compatible serialization proves old voice payloads without locale still work.

## Evidence required

- Schema/API excerpt showing additive `supported_locales` fields.
- Unit tests for valid and invalid BCP-47 tags.
- Serialization tests proving backward compatibility.

## Blocked by

None - can start immediately

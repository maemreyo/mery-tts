# Request locale field and backward-compatible API contract tests

Status: ready

## Parent

ADR-0039 — `docs/adr/ADR-0039-locale-and-language-contract.md`

## Type

AFK

## What to build

Add optional request-level `locale` selection for synthesis while preserving current missing-locale behavior. The speech request schema accepts an optional `locale` field validated against BCP-47 rules. When omitted, resolution falls back to the voice's default behavior. When provided with invalid format, a structured validation error is returned.

Behavioral contract: Clients can send `locale: "vi-VN"` (or omit it) with a synthesis request. The resolver later uses this to select voices. Missing locale follows existing behavior.

## Acceptance criteria

- [ ] Speech request schema accepts optional `locale` field without changing required fields.
- [ ] Missing locale falls back to voice default behavior.
- [ ] Request validation rejects malformed locale values with structured errors.
- [ ] Backward-compatible `/v1` serialization tests prove older clients remain compatible.
- [ ] API contract tests cover missing, valid, and invalid locale scenarios.

## Evidence required

- API contract test diff showing `/v1/audio/speech` accepts/returns locale correctly.
- Backward-compatible serialization test showing old client payload still works.
- Structured error taxonomy coverage for locale validation failures.

## Blocked by

01-voice-and-catalog-bcp47-locale-metadata-schema.md

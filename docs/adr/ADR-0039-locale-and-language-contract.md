# ADR-0039 — Locale and Language Contract

**Status:** Proposed
**Date:** 2026-06-11
**Source:** Grilling session — language selection and Vietnamese strategy

## Context

Mery is an offline-first local TTS runtime that must support more than one language without becoming a model-training project. The current runtime already has voice metadata, catalog projections, OpenAI-compatible speech, and provider adapters, but language/locale behavior needs to become explicit before Vietnamese or multilingual providers are added.

The roadmap research identifies language selection as a base gap and Vietnamese correctness as a product-critical concern. Locale handling affects catalog metadata, request validation, voice resolution, fallback, normalization, test fixtures, and console UX.

## Decision

Make locale/language a first-class contract in Mery.

Public API and catalog metadata use **BCP-47 locale tags** such as `vi-VN`, `en-US`, and `en-GB`. Internal helpers may derive broad language groups such as `vi` or `en`, but public contracts preserve region/accent/script distinctions.

Voices declare supported locales as metadata. Requests may express a desired locale. Voice metadata remains the source of truth; request locale constrains resolution. If a selected voice cannot serve the requested locale, Mery fails with a structured locale mismatch error by default. Fallback to a compatible locale/voice happens only when the request or configuration explicitly allows fallback.

Text normalization is a shared core preprocessing stage with adapter-specific final hooks:

- Core owns deterministic preprocessing: Unicode normalization, punctuation normalization, sentence segmentation, max-length handling, locale-aware safe transformations, and diagnostics metadata.
- Providers/adapters own model-specific phoneme/G2P quirks and final transformations.

Vietnamese support is contract-first and provider-driven. Mery does not train or fine-tune Vietnamese models in the near term. Future Vietnamese provider candidates can be evaluated, but the immediate work is locale metadata, normalization boundaries, resolver behavior, fixtures, and console UX.

Console UX exposes locale as a filter/display first. Normal users pick compatible voices; Developer Mode may later expose request-level locale override after backend validation is fully tested.

## Rationale

Silent cross-locale synthesis is a quality bug. A request for Vietnamese should not silently use an English voice. Explicit locale metadata and mismatch diagnostics make behavior predictable for users, developers, and future clients.

BCP-47 tags avoid locking Mery into coarse language-only behavior. They preserve distinctions such as `en-US` vs `en-GB` and give Vietnamese (`vi-VN`) a clear public contract.

Keeping normalization in a shared core stage prevents duplicated fixes across adapters while still allowing provider-specific final hooks. This keeps behavior testable and modular.

## Consequences

- Voice/catalog schemas need additive locale metadata.
- Request schemas may accept optional locale constraints without breaking `/v1` clients.
- Resolver diagnostics must include requested locale, selected voice locale, fallback reason, and blocked mismatch reasons.
- Locale support is not marked usable without fixtures for punctuation, numbers, abbreviations, diacritics, mixed-language text, long sentences, and malformed input.
- Fake-engine tests prove routing and normalization contracts; optional real-engine smoke proves audio viability.
- Console initially filters and displays locale; request override waits for Developer Mode and contract tests.

## Related

- [ADR-0013 — VoiceDescriptor discriminated union](ADR-0013-voice-descriptor-discriminated-union.md)
- [ADR-0014 — OpenAI-compatible speech layer](ADR-0014-openai-compatible-speech-layer.md)
- [ADR-0015 — Catalog model: normalized internal, flat external, artifact/voice identity](ADR-0015-catalog-model-artifact-voice-identity.md)
- [ADR-0022 — Provider fallback and synthesis orchestration](ADR-0022-provider-fallback-and-synthesis-orchestration.md)
- [ADR-0037 — Core Runtime Contract Before Console Expansion](ADR-0037-core-runtime-contract.md)
- `docs/reports/roadmap-research/axes/07-locale-and-text-normalization.md`

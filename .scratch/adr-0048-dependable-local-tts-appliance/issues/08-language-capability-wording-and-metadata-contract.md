# Language capability wording and metadata contract

Status: done
Type: AFK
Parent: .scratch/adr-0048-dependable-local-tts-appliance/PRD.md
ADR: docs/adr/ADR-0048-dependable-local-tts-appliance.md

## What to build

Make P1 language support honest and model-dependent across docs, launcher, API metadata, and tests. Mery should not claim universal language support or say the runtime globally supports a language unless catalog metadata, regression tests, and real-runtime smoke prove that locale. User-facing surfaces should say installed/catalog voices support specific locales.

P1 gates English real voice audio while preserving Vietnamese and broader locale correctness through BCP-47 metadata, normalization, and resolver tests.

## Acceptance criteria

- [x] User-facing docs/help avoid wording that implies Mery itself supports every language.
- [x] Launcher and readiness surfaces describe language support as installed/catalog voice locale capability.
- [x] API/catalog/voice metadata exposes locale information with BCP-47 tags where relevant.
- [x] English real voice remains the P1 audio happy path gate.
- [x] Vietnamese normalization/segmentation and locale mismatch behavior remain protected by deterministic tests.
- [x] Unsupported locale or voice mismatch behavior returns structured diagnostics rather than silently using an incompatible voice.
- [x] Tests cover language capability copy or metadata projections where feasible.

## Blocked by

- [02-launcher-readiness-wizard-foundation.md](02-launcher-readiness-wizard-foundation.md)

## Definition of Done evidence to record

- ADR/contract updated: yes/N/A — align with ADR-0039 if locale contract changes.
- fake-engine deterministic tests: yes — locale metadata/mismatch/normalization tests.
- API contract tests: yes if response metadata changes.
- CLI or Console proof: yes — launcher/help wording artifact.
- diagnostics/error sanitization tests: yes/N/A — locale diagnostics redaction review.
- docs/help updated: yes — language capability wording.
- optional real-engine smoke: N/A unless adding real locale model evidence.
- privacy gates: yes — no raw synthesis text in locale diagnostics.

## Evidence

- Implementation:
  - `src/mery_tts/schemas/v1.py` adds additive `LanguageSupportVo` and optional `VoiceSummary.language_support`.
  - `src/mery_tts/catalog/bundled.py` projects voice-specific BCP-47 language support for bundled catalog voices and marks only `piper-plus.en-us.lessac-low` as the P1 real-audio gate.
  - `src/mery_tts/api/app.py` includes language support for installed voice summaries.
  - `src/mery_tts/cli/launcher/services.py` adds readiness `language_support` with catalog locales, P1 gate voice/locale, and model-dependent wording.
  - `docs/reports/language-capability-contract.md` documents safe wording and forbids global/universal language claims.
- Deterministic tests:
  - `uv run pytest tests/contract/test_api_schemas.py tests/contract/test_bundled_catalog_wiring.py tests/cli/test_launch.py tests/unit/test_vietnamese_normalization_fixtures.py tests/contract/test_openai_speech.py -k 'locale or language or catalog_voices_expose or launch_bare_json or voice_summary'` → `16 passed, 71 deselected`.
  - Tests cover additive schema metadata, `/v1/catalog/voices` language support, launcher readiness language wording, and existing locale mismatch diagnostics.
- Static/typing gates:
  - `uv run ruff format --check src/mery_tts/schemas/v1.py src/mery_tts/catalog/bundled.py src/mery_tts/api/app.py src/mery_tts/cli/launcher tests/contract/test_api_schemas.py tests/contract/test_bundled_catalog_wiring.py tests/cli/test_launch.py` → `15 files already formatted`.
  - `uv run ruff check src/mery_tts/schemas/v1.py src/mery_tts/catalog/bundled.py src/mery_tts/api/app.py src/mery_tts/cli/launcher tests/contract/test_api_schemas.py tests/contract/test_bundled_catalog_wiring.py tests/cli/test_launch.py` → `All checks passed!`.
  - `uv run mypy src/mery_tts/schemas/v1.py src/mery_tts/catalog/bundled.py src/mery_tts/api/app.py src/mery_tts/cli/launcher` → `Success: no issues found in 12 source files`.
  - LSP diagnostics on modified schema/catalog/API/launcher/test files → no diagnostics after formatting/import fixes.
- CLI/API proof:
  - `uv run mery launch --action readiness --json` returned `data.language_support.scope: installed_or_catalog_voice`, catalog locales `en-US` and `vi-VN`, P1 gate locale `en-US`, P1 gate voice `piper-plus.en-us.lessac-low`, and wording: “Language support is model-dependent; choose an installed or catalog voice whose BCP-47 locale matches the text.”
  - A `TestClient` proof for `/v1/catalog/voices` returned baseline `language_support` as `{'scope': 'voice', 'supported_locales': ['en-US'], 'wording': 'Language support is specific to this installed or catalog voice.', 'p1_audio_gate': True}`.

## Definition of Done evidence

- ADR/contract updated: N/A — ADR-0048 already requires installed/catalog voice wording; additive contract documented in `docs/reports/language-capability-contract.md`.
- fake-engine deterministic tests: yes — schema/catalog/launcher and existing locale mismatch tests cover metadata and unsupported locale behavior without real downloads.
- API contract tests: yes — `tests/contract/test_api_schemas.py` and `tests/contract/test_bundled_catalog_wiring.py` cover additive API metadata.
- CLI or Console proof: yes — launcher readiness JSON proof recorded above.
- diagnostics/error sanitization tests: yes — existing OpenAI speech locale diagnostics tests remain in the focused gate and avoid raw synthesis text.
- docs/help updated: yes — language capability contract doc added.
- optional real-engine smoke: N/A — no new real locale model evidence added; English remains the P1 gate.
- privacy gates: yes — locale fields are BCP-47 tags only, not raw input text.

## Comments

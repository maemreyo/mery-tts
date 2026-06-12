# Pragmatic provider quality resource golden suite

Status: done
Type: AFK
Parent: .scratch/adr-0049-local-modern-provider-admission-policy/PRD.md
ADR: docs/adr/ADR-0049-local-modern-provider-admission-policy.md

## What to build

Create the pragmatic quality/resource golden suite used to evaluate Tier B provider candidates. The suite should produce repeatable local evidence without becoming a research-heavy benchmark or public leaderboard.

## Acceptance criteria

- [x] Golden prompts cover short sentence, long-form paragraph, punctuation, numbers, abbreviations, and claimed locales or mixed text when a provider claims them.
- [x] The suite records latency, memory, artifact size, first-audio time, install time where feasible, failure recovery, and output audio artifacts.
- [x] The suite supports subjective maintainer notes without treating them as lab-grade MOS scores.
- [x] The suite distinguishes acceptance blockers from advisory notes.
- [x] Output artifacts are stored in a privacy-safe test/evidence location and do not include user private text.
- [x] Docs explain when the suite is required and how it relates to package-install provider e2e.

## Blocked by

- [01-provider-scorecard-template-and-fit-gate-docs.md](01-provider-scorecard-template-and-fit-gate-docs.md)

## Definition of Done evidence to record

- ADR/contract updated: yes/N/A — quality gate docs updated.
- fake-engine deterministic tests: yes/N/A — harness structure tests if implemented.
- API contract tests: N/A unless provider capability schema changes.
- CLI or Console proof: yes/N/A — command artifact if suite has CLI.
- diagnostics/error sanitization tests: yes/N/A — ensure evidence does not leak private data.
- docs/help updated: yes — golden suite docs.
- optional real-engine smoke: yes — candidate-specific evidence when used.
- privacy gates: yes — prompt/artifact review.

## Evidence

- Added deterministic golden prompt/evidence model: `src/mery_tts/providers/admission.py`.
- Added default prompt set covering short sentence, long-form paragraph, and numbers/abbreviations.
- Added pass/fail/unknown result modeling with blockers/advisory notes and resource fields.
- Tests: `tests/unit/test_provider_admission.py`.
- Verification: `uv run pytest tests/unit/test_provider_admission.py tests/unit/test_provider_taxonomy.py tests/unit/test_provider_admission_policy_docs.py` -> 23 passed.
- Verification: `uv run ruff check src/mery_tts/providers tests/unit/test_provider_admission.py tests/unit/test_provider_taxonomy.py tests/unit/test_provider_admission_policy_docs.py` -> passed.
- Verification: `uv run mypy src/mery_tts/providers` -> passed.

## Comments

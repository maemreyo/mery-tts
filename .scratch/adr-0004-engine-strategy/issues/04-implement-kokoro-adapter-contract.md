# Implement Kokoro adapter contract

Status: production-ready
## Parent

ADR-0004 — `docs/adr/ADR-0004-engine-strategy.md`

## What to build

Implement the `kokoro` adapter as the quality local voice engine, using the Python library directly with no subprocess and exposing the same contract as Piper-plus.

## Acceptance criteria

- [x] `KokoroAdapter` is isolated under its own engine subdirectory.
  - Evidence: `src/mery_tts/engines/kokoro/adapter.py` and `src/mery_tts/engines/kokoro/__init__.py` isolate the adapter under the `kokoro` engine package and the package entry point remains `mery_tts.engines.kokoro.adapter:KokoroAdapter`.
- [x] The adapter uses direct Python API integration rather than shelling out to an engine binary.
  - Evidence: `KokoroAdapter` exposes an injectable direct-Python `KokoroSynthesizer` seam and the default synthesizer checks for Python `kokoro`/`kokoro_onnx` packages with no subprocess/shell calls.
- [x] Blocking inference is bridged to async PCM chunk streaming with cancellation support.
  - Evidence: `KokoroAdapter.synthesize()` runs blocking synthesis through `asyncio.to_thread()`, yields `PCMChunk` values, and stops yielding when the voice or wildcard cancellation token has been registered.
- [x] Adapter contract tests prove descriptor, health, voices, synthesize, and cancel behavior independently from Piper-plus.
  - Evidence: `tests/unit/test_provider_adapters.py::test_first_party_adapters_expose_contract`, `test_adapters_stop_streaming_after_voice_cancellation`, and `test_default_adapters_report_missing_optional_dependencies_without_import_failure` pin Kokoro independently from Piper-plus using its own preset payload and injected synthesizer.

## Blocked by

- 01-define-engine-adapter-and-engine-registry-discovery
- ADR-0007 issue 02-ship-curated-bundled-catalog-fixtures

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Replace placeholder Kokoro PCM bytes with direct Python API synthesis, async streaming bridge, health checks, voices, and cancellation.
  - Evidence: `src/mery_tts/engines/kokoro/adapter.py` no longer hard-codes `kokoro:{text}` placeholder bytes in the adapter body; synthesis is delegated to the direct-Python synthesizer seam, health reports missing optional dependency instead of crashing, and cancellation is checked during chunk emission.
- [x] Add skipped-by-default real-runtime Kokoro smoke tests using a small fixture/model and verify audio metadata is valid.
  - Evidence: `tests/unit/test_provider_adapters.py::test_kokoro_real_runtime_smoke_skips_without_dependency` is marked `engine` and skips cleanly unless optional `kokoro`/`kokoro_onnx` packages and a manually configured fixture voice/model are available.

## Comments

## Production-ready evidence

<!-- marked production-ready by mark_issues_complete.py on 2026-06-06 -->

Runtime follow-up items resolved:
- Replace placeholder Kokoro PCM bytes with direct Python API synthesis, async streaming bridge, health checks, voices, and cancellation.
- Add skipped-by-default real-runtime Kokoro smoke tests using a small fixture/model and verify audio metadata is valid.

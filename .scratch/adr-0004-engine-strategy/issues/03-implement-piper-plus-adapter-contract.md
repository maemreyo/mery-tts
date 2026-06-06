# Implement Piper-plus adapter contract

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0004 — `docs/adr/ADR-0004-engine-strategy.md`

## What to build

Implement the `piper-plus` adapter as the lightweight local voice engine, using the Python library directly with no subprocess and exposing the same contract as every engine.

## Acceptance criteria

- [x] `PiperPlusAdapter` is isolated under its own engine subdirectory.
  - Evidence: `src/mery_tts/engines/piper_plus/adapter.py` and `src/mery_tts/engines/piper_plus/__init__.py` isolate the adapter under the `piper_plus` engine package and the package entry point remains `mery_tts.engines.piper_plus.adapter:PiperPlusAdapter`.
- [x] The adapter uses direct Python API integration rather than shelling out to an engine binary.
  - Evidence: `PiperPlusAdapter` exposes an injectable direct-Python `PiperSynthesizer` seam and the default synthesizer checks for the Python `piper` package with no subprocess/shell calls.
- [x] Blocking inference is bridged to async PCM chunk streaming with cancellation support.
  - Evidence: `PiperPlusAdapter.synthesize()` runs blocking synthesis through `asyncio.to_thread()`, yields `PCMChunk` values, and stops yielding when the voice or wildcard cancellation token has been registered.
- [x] Adapter contract tests prove descriptor, health, voices, synthesize, and cancel behavior.
  - Evidence: `tests/unit/test_provider_adapters.py::test_first_party_adapters_expose_contract`, `test_adapters_stop_streaming_after_voice_cancellation`, and `test_default_adapters_report_missing_optional_dependencies_without_import_failure` pin descriptor acceptance, health, voices, synthesize, and cancel behavior.

## Blocked by

- 01-define-engine-adapter-and-engine-registry-discovery
- ADR-0007 issue 02-ship-curated-bundled-catalog-fixtures

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Replace placeholder Piper-plus PCM bytes with direct Python API synthesis, async streaming bridge, health checks, voices, and cancellation.
  - Evidence: `src/mery_tts/engines/piper_plus/adapter.py` no longer hard-codes `piper-plus:{text}` placeholder bytes in the adapter body; synthesis is delegated to the direct-Python synthesizer seam, health reports missing optional dependency instead of crashing, and cancellation is checked during chunk emission.
- [x] Add skipped-by-default real-runtime Piper-plus smoke tests using a small fixture/model and verify audio metadata is valid.
  - Evidence: `tests/unit/test_provider_adapters.py::test_piper_plus_real_runtime_smoke_skips_without_dependency` is marked `engine` and skips cleanly unless the optional `piper` package and a manually configured fixture model are available.

## Comments

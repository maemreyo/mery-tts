# Add runtime contract API and fake-engine gates

Status: completed

## Parent

ADR-0037 — `docs/adr/ADR-0037-core-runtime-contract.md`

## What to build

Add or consolidate contract tests that prove the runtime APIs used by the console behave consistently with fake engines and without real downloads. The completed slice should make core behavior verifiable before UI work depends on it.

## Acceptance criteria

- [x] The OpenAI-compatible speech path has fake-engine contract coverage for success, unsupported model/format, missing voice, fallback diagnostics, and sanitized error responses.
- [x] Streaming contract coverage proves first-chunk metadata, cancellation, sequence assignment, metadata drift behavior, and capability reporting without requiring a real engine.
- [x] Voice resolution coverage proves installed voice refresh behavior and unknown-voice failures through public interfaces.
- [x] Tests exercise FastAPI `/v1` surfaces where the console will depend on them, while lower-level service tests cover transport-neutral behavior.
- [x] The normal check path remains deterministic and does not require real engine packages, model downloads, or network access.

## Blocked by

- `issues/01-write-core-runtime-contract-document.md`

## Evidence

- Existing fake-engine runtime/API gates remain in `tests/contract/test_openai_speech.py`, `tests/unit/test_voice_resolver.py`, streaming unit tests, and FastAPI contract tests.
- `docs/architecture/core-runtime-contract.md` now records these gates as the required runtime evidence before Console work depends on `/v1`.
- `tests/unit/test_console_runtime_contract_docs.py` pins the documented fake-engine/default gate and optional real-engine smoke split.
- Verification: `uv run pytest tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py` — 31 passed.

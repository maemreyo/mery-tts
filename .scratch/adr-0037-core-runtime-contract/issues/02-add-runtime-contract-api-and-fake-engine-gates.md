# Add runtime contract API and fake-engine gates

Status: needs-triage

## Parent

ADR-0037 — `docs/adr/ADR-0037-core-runtime-contract.md`

## What to build

Add or consolidate contract tests that prove the runtime APIs used by the console behave consistently with fake engines and without real downloads. The completed slice should make core behavior verifiable before UI work depends on it.

## Acceptance criteria

- [ ] The OpenAI-compatible speech path has fake-engine contract coverage for success, unsupported model/format, missing voice, fallback diagnostics, and sanitized error responses.
- [ ] Streaming contract coverage proves first-chunk metadata, cancellation, sequence assignment, metadata drift behavior, and capability reporting without requiring a real engine.
- [ ] Voice resolution coverage proves installed voice refresh behavior and unknown-voice failures through public interfaces.
- [ ] Tests exercise FastAPI `/v1` surfaces where the console will depend on them, while lower-level service tests cover transport-neutral behavior.
- [ ] The normal check path remains deterministic and does not require real engine packages, model downloads, or network access.

## Blocked by

- `issues/01-write-core-runtime-contract-document.md`

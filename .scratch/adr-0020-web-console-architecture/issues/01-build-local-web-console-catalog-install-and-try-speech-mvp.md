# Build local web console catalog, install, and Try Speech MVP

Status: production-ready

## Parent

ADR-0020 — `docs/adr/ADR-0020-web-console-architecture.md`

## What to build

Build the first local web console milestone as a packaged static SPA served at `/console`. The milestone should let a local user enter the Mery token, browse catalog voice cards, start an install job, watch job polling, see installed state refresh, test speech with blocking WAV playback, and inspect diagnostics.

## Acceptance criteria

- [x] `/console` serves the packaged SPA and `/console/*` SPA fallback without affecting `/v1` routes; runtime does not require Node.js.
- [x] The frontend uses same-origin `/v1` calls with centralized bearer-token handling, memory token storage by default, and explicit opt-in persistence.
- [x] Catalog table lists voice cards, supports basic search/filter/sort, starts install by `catalogEntryId`, and polls job status until terminal state.
- [x] Try Speech selects an installed voice, sends `response_format=wav` and `stream=false`, plays the returned audio, and cleans up object URLs.
- [x] Diagnostics page renders engine/catalog/job error codes and messages from backend fixtures.
- [x] Frontend API/client/component/MSW tests and backend static-route tests cover the milestone without real downloads or real TTS engines.

## Blocked by

- ADR-0014 issue 01-implement-openai-compatible-blocking-speech-endpoint
- ADR-0016 issue 01-implement-async-install-job-manifest-commit-and-delete-gc

## Evidence

- `src/mery_tts/api/app.py` serves packaged static console assets at `/console`, `/console/assets/*`, and SPA fallback `/console/*`; middleware exempts console static routes while `/v1` routes still require bearer auth.
- `src/mery_tts/console/index.html`, `assets/app.css`, and `assets/app.js` are package-data-like Python package assets and run without a Node.js runtime.
- `assets/app.js` centralizes same-origin `fetch('/v1...')` calls, injects bearer auth, keeps tokens in memory by default, and persists only when the “Remember on this device” checkbox is selected.
- Catalog UI implements search/filter/sort, starts installs through `/v1/models/install`, and polls `/v1/models/install/{jobId}` until `completed` or `failed`.
- Try Speech posts `response_format: "wav"` and `stream: false` to `/v1/audio/speech`, plays the returned blob, and revokes old object URLs before reuse/unload.
- Diagnostics rendering reads `/v1/diagnostics` and shows backend check codes/messages.
- Focused verification: `uv run pytest tests/contract/test_api_core.py` → `13 passed`.

## Comments

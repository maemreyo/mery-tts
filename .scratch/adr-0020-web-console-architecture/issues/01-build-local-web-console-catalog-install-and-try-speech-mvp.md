# Build local web console catalog, install, and Try Speech MVP

Status: ready-for-human

## Parent

ADR-0020 — `docs/adr/ADR-0020-web-console-architecture.md`

## What to build

Build the first local web console milestone as a packaged static SPA served at `/console`. The milestone should let a local user enter the Mery token, browse catalog voice cards, start an install job, watch job polling, see installed state refresh, test speech with blocking WAV playback, and inspect diagnostics.

## Acceptance criteria

- [ ] `/console` serves the packaged SPA and `/console/*` SPA fallback without affecting `/v1` routes; runtime does not require Node.js.
- [ ] The frontend uses same-origin `/v1` calls with centralized bearer-token handling, memory token storage by default, and explicit opt-in persistence.
- [ ] Catalog table lists voice cards, supports basic search/filter/sort, starts install by `catalogEntryId`, and polls job status until terminal state.
- [ ] Try Speech selects an installed voice, sends `response_format=wav` and `stream=false`, plays the returned audio, and cleans up object URLs.
- [ ] Diagnostics page renders engine/catalog/job error codes and messages from backend fixtures.
- [ ] Frontend API/client/component/MSW tests and backend static-route tests cover the milestone without real downloads or real TTS engines.

## Blocked by

- ADR-0014 issue 01-implement-openai-compatible-blocking-speech-endpoint
- ADR-0016 issue 01-implement-async-install-job-manifest-commit-and-delete-gc

## Comments

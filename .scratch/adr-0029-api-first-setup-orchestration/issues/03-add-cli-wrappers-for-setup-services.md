# Add CLI wrappers for setup services

Status: completed

## Parent

ADR-0029 — `docs/adr/ADR-0029-api-first-setup-orchestration.md`

## What to build

Add CLI commands that wrap the same setup and voice pack services used by the API, so users can complete setup without the web console or Zam Reader.

## Acceptance criteria

- [x] `mery setup recommend` prints setup recommendations for optional client/intent inputs.
- [x] `mery voice-packs list` shows the same pack projection as `/v1/voice-packs`.
- [x] `mery voice-packs install <pack_id>` starts install through the same service path as the API.
- [x] CLI output clearly reports provider runtime requirements, download size, job status, and next smoke action.

## Production-ready criteria

- [x] CLI tests cover list, install success, invalid pack, missing provider runtime, and failed job output.
- [x] CLI does not reimplement install planning outside services.
- [x] Docs include terminal-only standalone setup flow.

## Blocked by

- ADR-0029 issue 01-add-setup-and-voice-pack-services

# Implement OpenAI-compatible blocking speech endpoint

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0014 — `docs/adr/ADR-0014-openai-compatible-speech-layer.md`

## What to build

Add the OpenAI-compatible `POST /v1/audio/speech` path as an edge adapter over native Mery voice resolution and synthesis. The first slice should support blocking WAV/PCM responses with deterministic alias resolution, Mery bearer-token auth reuse, explicit unsupported-parameter errors, and fake-adapter smoke coverage.

## Acceptance criteria

- [x] `POST /v1/audio/speech` accepts the MVP OpenAI-like request fields and rejects unsupported values explicitly.
- [x] OpenAI voice aliases resolve deterministically to configured native `voiceId` targets; missing targets return install/voice hints rather than fallback.
- [x] Native Mery errors are mapped to OpenAI-shaped error JSON only on this route.
- [x] Contract or SDK-style smoke tests prove a fake adapter can return blocking WAV or PCM bytes through the endpoint.

## Blocked by

- ADR-0013 issue 01-define-voice-descriptor-payload-union-and-adapter-kind-validation

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Return valid WAV bytes when `response_format=wav`; if unsupported, reject explicitly instead of returning raw PCM under a WAV request.
- [x] Use/request-validate `model`, voice alias configuration, response formats, request size/text limits, and OpenAI-shaped error mapping for all failures on this route. Format validation, voice alias resolution, request text-size limits, model allow-listing, and OpenAI-shaped route errors are covered.

## Comments

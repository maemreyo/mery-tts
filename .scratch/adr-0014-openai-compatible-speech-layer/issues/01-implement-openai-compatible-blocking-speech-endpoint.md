# Implement OpenAI-compatible blocking speech endpoint

Status: ready-for-agent

## Parent

ADR-0014 — `docs/adr/ADR-0014-openai-compatible-speech-layer.md`

## What to build

Add the OpenAI-compatible `POST /v1/audio/speech` path as an edge adapter over native Mery voice resolution and synthesis. The first slice should support blocking WAV/PCM responses with deterministic alias resolution, Mery bearer-token auth reuse, explicit unsupported-parameter errors, and fake-adapter smoke coverage.

## Acceptance criteria

- [ ] `POST /v1/audio/speech` accepts the MVP OpenAI-like request fields and rejects unsupported values explicitly.
- [ ] OpenAI voice aliases resolve deterministically to configured native `voiceId` targets; missing targets return install/voice hints rather than fallback.
- [ ] Native Mery errors are mapped to OpenAI-shaped error JSON only on this route.
- [ ] Contract or SDK-style smoke tests prove a fake adapter can return blocking WAV or PCM bytes through the endpoint.

## Blocked by

- ADR-0013 issue 01-define-voice-descriptor-payload-union-and-adapter-kind-validation

## Comments

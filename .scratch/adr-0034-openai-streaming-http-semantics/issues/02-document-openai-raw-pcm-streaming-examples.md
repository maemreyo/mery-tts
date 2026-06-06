# Document OpenAI raw PCM streaming examples

Status: pending

## Parent

ADR-0034 — `docs/adr/ADR-0034-openai-streaming-http-semantics.md`

## What to build

Add integration documentation and examples that teach clients how to consume Mery's raw PCM HTTP stream safely without mistaking it for a WAV file or browser-playable media URL.

## Acceptance criteria

- [ ] Documentation explains `stream=true + response_format=pcm` response semantics and headers.
- [ ] Python example under `examples/openai_streaming/` consumes the stream and writes raw PCM bytes to disk.
- [ ] Node example under `examples/openai_streaming/` consumes the stream and writes raw PCM bytes to disk.
- [ ] Docs explicitly state raw PCM is not WAV and browser raw PCM playback is deferred until a Web Audio helper exists.

## Production-ready criteria

- [ ] Examples are copy-pasteable against localhost with bearer token configuration.
- [ ] `docs/integration/openai-streaming.md` links to the examples.
- [ ] Docs include conversion/playback caveats for sample rate, channels, and signed 16-bit little-endian PCM.
- [ ] Existing integration docs link to the streaming guide.

## Blocked by

- `01-emit-audio-l16-first-chunk-derived-http-stream.md`

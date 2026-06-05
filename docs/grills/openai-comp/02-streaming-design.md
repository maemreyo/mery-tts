# Grill 02 — P1 Streaming Design for OpenAI-Compatible Speech

**Date:** 2026-06-05
**Status:** Q20–Q27 recommended, awaiting user confirmation
**Trigger:** After Grill 01 chose P1 chunked HTTP streaming as the next feature after P0 OpenAI-compatible blocking speech
**Parent decision file:** `docs/grills/openai-comp/01-voice-descriptor-and-engine-selection.md`

---

## Decision tree so far

- **Q19** — Next feature after P0: chunked HTTP streaming for `/v1/audio/speech` (recorded in Grill 01)
- **Q20** — Streaming response format: raw PCM first vs. WAV streaming vs. event formats
- **Q21** — Streaming cancellation semantics: route catches disconnect, adapter cancel is idempotent
- **Q22** — Chunk metadata source: self-contained PCMChunk with stream stability validation
- **Q23** — Backpressure policy: bounded queue with producer backpressure and cancellation guardrail
- **Q24** — Streaming error behavior: JSON before first byte, terminate/log after stream starts
- **Q25** — Streaming client examples: staged Python + Node first, browser after playback helper
- **Q26** — Streaming implementation slice: vertical tracer bullet, not route-first or primitive-only
- **Q27** — P1 streaming definition of done: protocol-complete with optional real-engine release gate
- Q28+ — TBD as we walk down the streaming design tree

---

## Q20 — Streaming response format

**Verdict:** Support **raw PCM streaming first** for `stream=true`. Do not start with WAV streaming, NDJSON, SSE, or WebSocket for the OpenAI-compatible endpoint.

Recommended P1 support matrix:

```text
stream=false + response_format=wav -> blocking full WAV response (P0 path)
stream=false + response_format=pcm -> blocking full raw PCM response
stream=true  + response_format=pcm -> chunked HTTP raw PCM streaming (P1 first target)
stream=true  + response_format=wav -> explicit unsupported initially
stream=true  + response_format=mp3/opus/aac/flac -> explicit unsupported until encoders exist
```

**Response headers for raw PCM streaming:**

```text
Content-Type: audio/L16; rate=24000; channels=1
X-Mery-Audio-Format: pcm_s16le
X-Mery-Sample-Rate: 24000
X-Mery-Channels: 1
X-Mery-Frame-Duration-Ms: 20
```

The exact sample rate should come from `PCMChunk` / `VoiceDescriptor` / adapter output metadata, not a hardcoded route constant. `24000` is the default/example, not a universal invariant.

**Options considered:**

| Option | Design | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | `stream=true` supports raw PCM chunks first | Correct, low-latency, no fake container header, no base64 overhead | Client must read sample-rate/channel metadata | ✅ P1 first |
| B | Streaming WAV with unknown/large data-size header | Familiar file/container format | Compatibility is player-dependent; header needs final length or nonstandard workaround | ❌ defer |
| C | NDJSON chunks `{ audio: base64 }` | Metadata-rich and debuggable | Not direct audio stream; base64 overhead; client must decode events | ❌ not for OpenAI audio route |
| D | SSE events | Observable and event-friendly | Not OpenAI audio-compatible; duplicates native WS/event concepts | ❌ |

**Why raw PCM first wins:**

| Criterion | Why this wins |
|---|---|
| Flexible | Works for fake, Piper, Kokoro, and future engines because all normalize to PCM chunks |
| Clean | HTTP stream body contains audio bytes only; metadata lives in headers |
| SoC | Route owns transport/headers; adapter owns PCM generation; encoder only passes/normalizes PCM bytes |
| Modular | Adding WAV/MP3 later is an encoder capability, not a change to EngineAdapter or VoiceRegistry |
| Standalone | Tests run with fake PCM chunks; no external codec binaries, real engines, or network needed |
| Scalable | Avoids container-specific edge cases while provider count grows |
| Well-tested | Chunk order, metadata headers, first-chunk timing, unsupported format errors, and disconnect cancellation are all deterministic |

**Recommended route behavior:**

```text
POST /v1/audio/speech
  { "model": "tts-1", "voice": "alloy", "input": "Hello", "response_format": "pcm", "stream": true }

Flow:
  OpenAISpeechRequest validates stream=true + response_format=pcm
  -> resolver maps model/voice to native VoiceDescriptor
  -> VoiceRegistry.resolve(...)
  -> adapter.synthesize(...) yields AsyncIterator[PCMChunk]
  -> StreamingResponse yields raw pcm_s16le bytes per chunk
  -> client disconnect calls adapter.cancel(session_id)
```

**Recommended schema validation:**

```python
class OpenAISpeechRequest(BaseModel):
    model: str | None = None
    input: str
    voice: str
    response_format: Literal["wav", "pcm"] = "wav"
    speed: float = Field(default=1.0, ge=0.25, le=4.0)
    stream: bool = False

    @model_validator(mode="after")
    def validate_streaming_format(self) -> Self:
        if self.stream and self.response_format != "pcm":
            raise UnsupportedOpenAIParameter(
                param="response_format",
                code="unsupported_streaming_response_format",
                message="Mery P1 supports stream=true only with response_format=pcm.",
            )
        return self
```

**Boundary rule:** Do not introduce a new event protocol for this route. `POST /v1/audio/speech` remains an audio endpoint. If the client wants structured Mery events, use native `WS /v1/events`; if it wants OpenAI-compatible speech streaming, use chunked HTTP audio bytes.

```text
/v1/audio/speech stream=true -> direct audio byte stream
/v1/events                   -> native Mery event stream
```

**Files affected when implementing:**

| File | Change |
|---|---|
| `src/mery_tts/openai_compat/schemas.py` | Add/validate `stream=true` + `response_format=pcm` only |
| `src/mery_tts/api/routes/openai_speech.py` | Add StreamingResponse branch for raw PCM |
| `src/mery_tts/audio/encoder.py` | Add streaming PCM pass-through/normalizer helper if needed |
| `src/mery_tts/schemas/v1/audio.py` or existing PCM schema | Ensure PCMChunk exposes sample rate/channels/format metadata |
| `tests/unit/openai_compat/test_streaming_request_schema.py` | Validation matrix for stream/format combinations |
| `tests/contract/api/test_openai_speech_streaming.py` | Chunked response, headers, fake PCM chunks, disconnect cancellation |

**Testing requirements:**

```text
1. stream=true + response_format=pcm returns chunked response with Content-Type audio/L16
2. Response headers include sample rate, channels, and PCM format
3. Fake adapter yields multiple chunks; client receives chunks in order
4. First chunk is yielded before fake adapter completes all chunks
5. stream=true + response_format=wav returns OpenAI-shaped unsupported_streaming_response_format before synthesis starts
6. stream=true + response_format=mp3/opus/aac/flac returns unsupported_response_format before synthesis starts
7. Client disconnect calls adapter.cancel(session_id)
8. Blocking stream=false path remains unchanged
9. No test requires real engine packages, model files, OpenAI cloud, or Zam Reader
```

**Recommendation nuance:** Raw PCM is less friendly than WAV as a file format, but it is the correct first streaming transport. WAV is a container with header/final-length concerns; raw PCM is already what the engine contract produces. Start with the clean byte stream, then add tested container/codecs later.

---

## Q21 — Streaming cancellation semantics

**Verdict:** The HTTP route/generator owns client disconnect detection; the engine adapter owns synthesis cancellation. On cancellation, the route calls `adapter.cancel(session_id)`. Adapter cancellation must be idempotent and safe to call from `except` and `finally` paths.

**Recommended flow:**

```text
client disconnects HTTP stream
  -> StreamingResponse generator receives cancellation / disconnect signal
  -> route calls adapter.cancel(session_id)
  -> adapter/model_runner marks CancelToken cancelled
  -> blocking synthesis bridge stops yielding more chunks when possible
  -> route exits without logging a false 500
```

**Options considered:**

| Option | Design | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Ignore disconnect; engine keeps generating | Simplest | Wastes CPU/RAM; bad for long text and voice-agent loops | ❌ |
| B | Route catches disconnect/cancel and calls `adapter.cancel(session_id)` | Clean boundary; uses existing adapter contract | Needs careful generator tests | ✅ P1 |
| C | Add global cancellation manager outside adapters | Powerful | Extra infrastructure before needed; overlaps adapter/session lifecycle | ❌ defer |
| D | Kill worker thread/process | Forceful | Unsafe for Python libs; can corrupt model state | ❌ |

**Recommended route sketch:**

```python
async def stream_pcm_response(
    adapter: EngineAdapter,
    voice: VoiceDescriptor,
    text: str,
    session_id: str,
) -> AsyncIterator[bytes]:
    try:
        async for chunk in adapter.synthesize(text=text, voice=voice, session_id=session_id):
            yield chunk.pcm_bytes
    except asyncio.CancelledError:
        await adapter.cancel(session_id)
        raise
    except Exception:
        await adapter.cancel(session_id)
        raise
    finally:
        # Idempotent cleanup. Safe if synthesis finished normally or cancel already happened.
        await adapter.cancel(session_id)
```

If FastAPI/Starlette exposes request disconnect checks in the chosen implementation, the generator may also poll `await request.is_disconnected()` between chunks, but that should be treated as a transport optimization, not the only cancellation mechanism.

**Adapter/model runner contract:**

```python
class EngineAdapter(ABC):
    async def cancel(self, session_id: str) -> None:
        """Idempotently request cancellation for an active or already-finished session."""
```

Model runner pattern:

```python
class ModelRunner:
    _cancel_tokens: dict[str, CancelToken]

    async def synthesize_stream(..., session_id: str) -> AsyncIterator[PCMChunk]:
        token = CancelToken()
        self._cancel_tokens[session_id] = token
        try:
            # bridge blocking inference -> async queue
            ...
        finally:
            self._cancel_tokens.pop(session_id, None)

    async def cancel(self, session_id: str) -> None:
        token = self._cancel_tokens.get(session_id)
        if token is not None:
            token.cancel()
```

**Why B wins:**

| Criterion | Why this wins |
|---|---|
| Flexible | Works for fake, Piper, Kokoro, and future engines as long as they implement adapter cancellation |
| Clean | HTTP disconnect remains a transport concern; model cancellation remains adapter concern |
| SoC | Route does not manipulate engine threads/tokens directly; adapter does not know HTTP exists |
| Modular | No global cancellation service required for P1; future manager can be added if multiple transports need it |
| Standalone | Cancellation tests use fake delayed chunks; no real engine, network, or browser needed |
| Scalable | Prevents abandoned long syntheses from consuming resources under voice-agent workloads |
| Well-tested | Idempotency, normal completion, mid-stream disconnect, and adapter error cases can be covered deterministically |

**Error/logging rule:** Client disconnect is not a server error. It should be logged at debug/info with structured context, not as stacktrace noise.

```text
log event: openai_speech.stream_cancelled
fields: session_id, voice_id, engine_id, reason=client_disconnect
level: info or debug
```

**Files affected when implementing:**

| File | Change |
|---|---|
| `src/mery_tts/api/routes/openai_speech.py` | Streaming generator catches cancellation and calls adapter.cancel |
| `src/mery_tts/engines/base.py` | Document cancel idempotency requirement |
| `src/mery_tts/engines/*/model_runner.py` | Ensure cancel token cleanup is idempotent |
| `tests/contract/api/test_openai_speech_streaming.py` | Client disconnect cancellation tests |
| `tests/unit/engines/test_cancel_idempotency.py` | Fake/model runner cancel idempotency |

**Testing requirements:**

```text
1. Normal stream completion calls cleanup and leaves no cancel token behind
2. Client disconnect/cancel calls adapter.cancel(session_id)
3. adapter.cancel(session_id) can be called twice without error
4. Fake adapter stops yielding after cancellation
5. Cancellation does not produce OpenAI JSON error after chunks have already started
6. Cancellation is logged as stream_cancelled, not server error
7. Blocking stream=false path is unaffected
```

**Recommendation nuance:** This uses the existing `EngineAdapter.cancel(session_id)` abstraction correctly. If later Native WS, HTTP streaming, and CLI playback all need shared cancellation orchestration, add a manager then. P1 should not introduce that infrastructure prematurely.

---

## Q22 — Chunk metadata source

**Verdict:** Every `PCMChunk` should carry audio metadata (`sample_rate`, `channels`, `sample_width_bytes`, `format`, `sequence`). The streaming route should validate metadata stability across the stream before/while emitting headers and chunks. This makes chunks self-contained, testable, and adapter-independent.

**Recommended schema:**

```python
class PCMChunk(BaseModel):
    data: bytes
    sample_rate: int = Field(gt=0)
    channels: int = Field(gt=0)
    sample_width_bytes: Literal[2] = 2
    format: Literal["pcm_s16le"] = "pcm_s16le"
    sequence: int = Field(ge=0)
```

**Streaming route behavior:**

```text
1. Pull first PCMChunk from adapter.synthesize(...)
2. Use first chunk metadata to set response headers
3. Emit first chunk bytes
4. For every subsequent chunk:
   - validate sample_rate/channels/sample_width/format match first chunk
   - validate sequence is monotonic if sequence is provided/required
   - emit bytes
5. If metadata changes mid-stream, cancel adapter and terminate stream/log structured error
```

Headers from first chunk:

```text
Content-Type: audio/L16; rate={sample_rate}; channels={channels}
X-Mery-Audio-Format: pcm_s16le
X-Mery-Sample-Rate: {sample_rate}
X-Mery-Channels: {channels}
X-Mery-Sample-Width-Bytes: 2
```

**Options considered:**

| Option | Design | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Every `PCMChunk` carries metadata | Self-contained; robust across engines; easiest fixtures | Repeated metadata; must validate stability | ✅ P1 |
| B | `VoiceDescriptor` carries output format | Clean for fixed-output voices | Engines/backends may vary actual output; stale metadata risk | ❌ |
| C | `EngineDescriptor` carries default output format | Simple | Too coarse for per-voice/per-model differences | ❌ |
| D | First chunk metadata object, later chunks bytes only | Efficient | Invents more complex stream protocol | ❌ defer |

**Why A wins:**

| Criterion | Why this wins |
|---|---|
| Flexible | Each adapter can truthfully emit actual output metadata, even if voice/backend differs |
| Clean | `PCMChunk` is the audio unit; it carries enough data to be encoded or streamed independently |
| SoC | Adapters own audio facts; route owns header derivation and stability validation; encoder owns byte formatting |
| Modular | Future engines do not need global config to describe their chunks |
| Standalone | Fake adapter can emit deterministic chunks with metadata; tests require no real engine |
| Scalable | More providers can vary sample rates without changing route constants |
| Well-tested | Unit tests can validate chunk schema, stability checker, and route header derivation separately |

**Recommended helper:**

```python
class PCMStreamMetadata(BaseModel):
    sample_rate: int
    channels: int
    sample_width_bytes: Literal[2]
    format: Literal["pcm_s16le"]

    @classmethod
    def from_chunk(cls, chunk: PCMChunk) -> Self: ...

    def assert_matches(self, chunk: PCMChunk) -> None:
        if (
            self.sample_rate != chunk.sample_rate
            or self.channels != chunk.channels
            or self.sample_width_bytes != chunk.sample_width_bytes
            or self.format != chunk.format
        ):
            raise AudioStreamMetadataChanged(...)
```

**Boundary rule:** `EngineDescriptor` and `VoiceDescriptor` may expose *declared* or *expected* audio capabilities, but streaming headers must come from the actual emitted `PCMChunk` metadata.

```text
EngineDescriptor -> capability/default info for clients
VoiceDescriptor  -> voice metadata and payload
PCMChunk         -> actual audio stream metadata used for response headers
```

**Files affected when implementing:**

| File | Change |
|---|---|
| `src/mery_tts/schemas/v1/audio.py` | Define/extend `PCMChunk` with metadata and sequence |
| `src/mery_tts/audio/streaming.py` | NEW helper: PCMStreamMetadata/stability validation |
| `src/mery_tts/audio/encoder.py` | Use chunk metadata for WAV/PCM encoding as needed |
| `src/mery_tts/api/routes/openai_speech.py` | Derive streaming headers from first chunk metadata |
| `tests/unit/audio/test_pcm_chunk_schema.py` | Chunk metadata validation |
| `tests/unit/audio/test_stream_metadata.py` | Stability checker tests |
| `tests/contract/api/test_openai_speech_streaming.py` | Headers reflect fake chunk metadata |

**Testing requirements:**

```text
1. PCMChunk rejects invalid sample_rate/channels and unsupported sample width/format
2. First chunk metadata produces expected audio/L16 content-type and X-Mery headers
3. Subsequent matching chunks stream successfully
4. Metadata change mid-stream triggers cancellation and structured log
5. sequence values are monotonic in fake adapter stream
6. Route does not hardcode 24000 Hz; fake adapter can test 16000 and 24000
7. Blocking WAV encoder can use same chunk metadata for header generation
```

**Recommendation nuance:** Repeating metadata in every chunk is a tiny overhead compared to audio bytes and gives a major correctness benefit. It prevents route-level hardcoding and makes every adapter independently testable.

---

## Q23 — Backpressure policy

**Verdict:** Use a **bounded queue with producer backpressure**, plus a timeout/cancellation guardrail for stalled clients. Never use an unbounded queue and never drop audio chunks.

Recommended core rule:

```text
client slower than engine
  -> bounded queue fills
  -> producer blocks/waits
  -> if wait exceeds threshold or client disconnects, cancel session
  -> no chunk dropping, no memory growth without bound
```

**Recommended queue shape:**

```python
queue: asyncio.Queue[PCMChunk | None] = asyncio.Queue(maxsize=8)
```

`maxsize=8` is a starting default, not a protocol guarantee. It should be configurable later if needed, but P1 can keep it as an internal constant with tests.

**Options considered:**

| Option | Design | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Unbounded queue | Simple implementation | Memory leak risk under slow clients/long text | ❌ |
| B | Bounded queue + producer backpressure | Safe memory behavior; preserves audio correctness | Producer may block while client is slow | ✅ base policy |
| C | Drop old chunks | Keeps latency | Corrupts audio; unacceptable for speech stream | ❌ |
| D | Cancel if queue remains full too long | Protects server under pathological clients | Harsh if threshold too low | ✅ guardrail |

**Why B + D wins:**

| Criterion | Why this wins |
|---|---|
| Flexible | Works for fake adapter, thread-backed Piper/Kokoro, and future async-native engines |
| Clean | Backpressure lives in the blocking-to-async bridge/model runner, not in API route hacks |
| SoC | Route streams bytes; model runner mediates queueing; adapter owns cancellation token |
| Modular | Every engine can reuse the same bridge pattern or implement equivalent bounded streaming |
| Standalone | Tests use fake slow client / fast producer without real engine or network |
| Scalable | Prevents runaway memory when many clients stream or clients read slowly |
| Well-tested | Queue full, timeout, cancellation, and no-drop ordering can be tested deterministically |

**Recommended producer bridge pattern:**

```python
QUEUE_MAX_CHUNKS = 8
QUEUE_PUT_TIMEOUT_SECONDS = 5.0

async def put_with_backpressure(
    queue: asyncio.Queue[PCMChunk | None],
    chunk: PCMChunk,
    token: CancelToken,
) -> None:
    if token.is_cancelled:
        raise SynthesisCancelled()
    try:
        await asyncio.wait_for(queue.put(chunk), timeout=QUEUE_PUT_TIMEOUT_SECONDS)
    except TimeoutError as exc:
        token.cancel()
        raise StreamBackpressureTimeout() from exc
```

For thread-backed inference that uses `loop.call_soon_threadsafe`, avoid blind `put_nowait` into a bounded queue because it can fail or spin. Prefer a bridge that respects capacity, or uses `asyncio.run_coroutine_threadsafe(queue.put(chunk), loop)` and waits with timeout from the worker side.

**Thread-backed runner nuance:**

```python
future = asyncio.run_coroutine_threadsafe(queue.put(chunk), loop)
try:
    future.result(timeout=QUEUE_PUT_TIMEOUT_SECONDS)
except TimeoutError:
    token.cancel()
    break
```

This lets the blocking inference worker slow down when the HTTP consumer is slow. That is safer than allocating unbounded memory.

**Consumer behavior:**

```python
async for chunk in adapter.synthesize(...):
    yield chunk.data
```

The HTTP response generator naturally applies downstream backpressure because it only requests the next chunk when it can yield. The queue mainly protects the sync-engine bridge where generation and async HTTP consumption are decoupled.

**No-drop rule:**

```text
Do not drop PCM chunks.
Dropping chunks corrupts audio timing/content and creates hard-to-debug playback artifacts.
If the system cannot keep up, cancel cleanly rather than producing corrupted audio.
```

**Files affected when implementing:**

| File | Change |
|---|---|
| `src/mery_tts/engines/base.py` | Document bounded backpressure expectation for streaming adapters |
| `src/mery_tts/engines/*/model_runner.py` | Bounded queue + timeout guard for sync-to-async bridge |
| `src/mery_tts/audio/streaming.py` | Optional shared helpers/constants for queue/backpressure validation |
| `src/mery_tts/api/routes/openai_speech.py` | Propagate cancellation; do not buffer whole stream in route |
| `tests/unit/audio/test_backpressure.py` | Queue full/timeout/no-drop behavior with fake producer |
| `tests/contract/api/test_openai_speech_streaming.py` | Slow-consumer/cancel behavior at route level |

**Testing requirements:**

```text
1. Fast producer + slow consumer never creates unbounded queue growth
2. Queue maxsize is enforced in fake runner test
3. Chunks are delivered in sequence order; none are dropped under normal backpressure
4. Queue put timeout cancels session and stops producer
5. Client disconnect cancels before queue timeout when disconnect is detected
6. Backpressure timeout is logged as stream_backpressure_timeout, not generic 500 noise
7. Blocking stream=false path does not use streaming queue/backpressure code
```

**Recommendation nuance:** Backpressure is a correctness feature, not just resource protection. For audio, preserving ordered bytes matters more than shaving latency by dropping chunks. If a client is too slow, cancel explicitly instead of corrupting playback.

---

## Q24 — Streaming error behavior

**Verdict:** Use strict HTTP semantics: before the first audio byte is emitted, return an OpenAI-shaped JSON error; after the first audio byte is emitted, terminate the stream, cancel the adapter, and write a structured log. Do not wrap audio chunks in NDJSON, do not append custom trailers, and do not emit silence to hide errors.

**Core rule:**

```text
Before first byte -> normal OpenAI JSON error response
After first byte  -> terminate audio stream + cancel adapter + structured log
```

**Why this distinction exists:** Once the route has sent audio headers and body bytes, the response is already an audio stream. The server cannot reliably switch the response into JSON error mode without corrupting the protocol.

**Options considered:**

| Option | Design | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | JSON error before first chunk; terminate/log after first chunk | Correct HTTP semantics; keeps body as audio bytes | Client sees truncated audio for mid-stream failure | ✅ P1 |
| B | Wrap all chunks in NDJSON with error events | Can represent mid-stream errors | Not direct audio stream; base64 overhead; breaks OpenAI-style audio route | ❌ |
| C | Append custom HTTP trailers | Theoretically preserves audio stream + error metadata | Poor client/proxy support; hard to test portably | ❌ |
| D | Swallow error and emit silence | Playback may continue | Hides failures; corrupts meaning/timing; bad observability | ❌ |

**Recommended implementation shape:**

```python
async def create_streaming_response(...) -> Response:
    try:
        first_chunk = await anext(chunk_iter)
    except LocalTTSError as exc:
        status, body = map_mery_error_to_openai(exc)
        return JSONResponse(status_code=status, content=body.model_dump())

    metadata = PCMStreamMetadata.from_chunk(first_chunk)

    async def body() -> AsyncIterator[bytes]:
        stream_started = False
        try:
            nonlocal first_chunk
            yield first_chunk.data
            stream_started = True

            async for chunk in chunk_iter:
                metadata.assert_matches(chunk)
                yield chunk.data
        except asyncio.CancelledError:
            await adapter.cancel(session_id)
            log.info("openai_speech.stream_cancelled", session_id=session_id, reason="client_disconnect")
            raise
        except Exception as exc:
            await adapter.cancel(session_id)
            if stream_started:
                log.warning(
                    "openai_speech.stream_failed_after_start",
                    session_id=session_id,
                    voice_id=voice.voice_id,
                    engine_id=voice.engine_id,
                    error=str(exc),
                )
                return
            raise
        finally:
            await adapter.cancel(session_id)

    return StreamingResponse(body(), media_type=metadata.content_type())
```

**Important nuance:** The route should attempt to pull the first chunk before constructing the final `StreamingResponse` when practical. This lets pre-audio failures return clean JSON instead of creating a stream that immediately fails.

**Pre-first-byte failures:**

```text
alias invalid                  -> 400 OpenAI JSON error
native voice_id not found      -> 400 OpenAI JSON error
engine unavailable             -> 503 OpenAI JSON error
unsupported stream format      -> 400 OpenAI JSON error
adapter fails before audio     -> mapped OpenAI JSON error if LocalTTSError, else 500 server_error
```

**Post-first-byte failures:**

```text
engine raises after chunk N          -> terminate stream, cancel adapter, log stream_failed_after_start
metadata changes after chunk N       -> terminate stream, cancel adapter, log audio_metadata_changed
backpressure timeout after chunk N   -> terminate stream, cancel adapter, log stream_backpressure_timeout
client disconnect                    -> cancel adapter, log stream_cancelled, no error response
```

**Why A wins:**

| Criterion | Why this wins |
|---|---|
| Flexible | Works for any binary audio format without inventing an envelope protocol |
| Clean | Preserves HTTP/body semantics: JSON errors only when response has not become audio yet |
| SoC | Error mapper handles pre-stream errors; streaming generator handles post-start lifecycle/logging |
| Modular | Engine adapters still only raise/cancel; they do not know about HTTP response states |
| Standalone | Fake adapter can deterministically fail before first chunk or after N chunks in tests |
| Scalable | Avoids format-specific hacks as more engines and encoders are added |
| Well-tested | Both pre-first-byte and post-first-byte cases are deterministic test fixtures |

**Logging events:**

```text
openai_speech.stream_failed_before_start
openai_speech.stream_failed_after_start
openai_speech.stream_cancelled
openai_speech.audio_metadata_changed
openai_speech.stream_backpressure_timeout
```

Each event should include:

```text
session_id
request_id if available
voice_id
engine_id
chunk_sequence if available
error_code / exception_class
```

**Files affected when implementing:**

| File | Change |
|---|---|
| `src/mery_tts/api/routes/openai_speech.py` | First-chunk prefetch, response-state-aware streaming generator |
| `src/mery_tts/openai_compat/errors.py` | Pre-first-byte error mapping remains unchanged |
| `src/mery_tts/audio/streaming.py` | Metadata stability errors and helper exceptions |
| `tests/contract/api/test_openai_speech_streaming_errors.py` | Before/after first chunk failure cases |
| `tests/unit/audio/test_stream_metadata.py` | Metadata-changed error behavior |

**Testing requirements:**

```text
1. Fake adapter raises before first chunk -> OpenAI-shaped JSON error and no audio headers
2. Fake adapter yields one chunk then raises -> response starts as audio and terminates without JSON body
3. Metadata change after first chunk -> stream terminates and logs audio_metadata_changed
4. Backpressure timeout after stream starts -> stream terminates, adapter.cancel called, structured log emitted
5. Client disconnect -> adapter.cancel called and no server-error log
6. No NDJSON/SSE/trailer behavior exists on /v1/audio/speech streaming path
7. Blocking stream=false error behavior remains unchanged
```

**Recommendation nuance:** Mid-stream binary errors are inherently less expressive than event streams. That is acceptable because `/v1/audio/speech` is an audio endpoint. Clients that need structured progress/error events should use native `WS /v1/events`, not force event semantics into the OpenAI-compatible audio route.

---

## Q25 — Streaming client examples

**Verdict:** Provide staged examples: Python `httpx.stream()` first, Node.js stream-to-file second, browser example later only after a proper raw PCM Web Audio playback helper exists. Do not ship browser raw PCM playback as a half-working snippet.

**Recommended staging:**

```text
P1 docs/examples:
  1. Python httpx stream -> raw PCM file
  2. Python httpx stream -> sounddevice playback helper
  3. Node.js fetch stream -> raw PCM file

P1.5/P2 docs/examples:
  4. Browser fetch ReadableStream -> Web Audio playback helper
```

**Options considered:**

| Option | Design | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Python `httpx.stream()` only | Simple and easy to verify | Misses JS/Node ecosystem | ⚠️ too narrow alone |
| B | Browser `fetch()` only | Web-app relevant | Raw PCM playback is easy to get wrong | ❌ defer |
| C | Python + Node now, browser after helper | Practical coverage while avoiding bad browser snippet | More docs/tests than Python-only | ✅ staged |
| D | No examples until SDK exists | Keeps scope small | Users struggle with raw PCM streaming | ❌ |

**Why staged C wins:**

| Criterion | Why this wins |
|---|---|
| Flexible | Examples cover CLI/server developers first and leave room for browser playback later |
| Clean | Docs do not pretend raw PCM browser playback is trivial |
| SoC | HTTP streaming examples stay separate from audio playback helper implementation |
| Modular | Python, Node, and browser examples can live as independent docs/scripts |
| Standalone | Python/Node examples run against local Mery only; no cloud/OpenAI/Zam Reader needed |
| Scalable | Future SDKs can replace examples without changing protocol docs |
| Well-tested | Python/Node examples can be smoke-tested; browser helper can wait for dedicated playback tests |

**Recommended docs location:**

```text
docs/integration/openai-compat.md
  - short streaming section + links

docs/integration/openai-streaming.md
  - detailed P1 streaming examples
  - raw PCM format explanation
  - Python examples
  - Node examples
  - browser status/roadmap

examples/openai_streaming/
  stream_pcm_httpx.py
  play_pcm_httpx.py
  stream_pcm_node.mjs
```

**Python stream-to-file example:**

```python
import httpx

MERY_TOKEN = "<mery-token>"

with httpx.stream(
    "POST",
    "http://127.0.0.1:8765/v1/audio/speech",
    headers={"Authorization": f"Bearer {MERY_TOKEN}"},
    json={
        "model": "tts-1",
        "voice": "alloy",
        "input": "Hello from streaming Mery",
        "response_format": "pcm",
        "stream": True,
    },
    timeout=None,
) as response:
    response.raise_for_status()
    sample_rate = int(response.headers["X-Mery-Sample-Rate"])
    channels = int(response.headers["X-Mery-Channels"])
    print("PCM", sample_rate, channels)

    with open("speech.pcm", "wb") as file:
        for chunk in response.iter_bytes():
            file.write(chunk)
```

**Python playback helper example:**

```python
import httpx
import numpy as np
import sounddevice as sd

with httpx.stream(...same request...) as response:
    response.raise_for_status()
    sample_rate = int(response.headers["X-Mery-Sample-Rate"])
    channels = int(response.headers["X-Mery-Channels"])

    with sd.OutputStream(samplerate=sample_rate, channels=channels, dtype="int16") as stream:
        for chunk in response.iter_bytes():
            audio = np.frombuffer(chunk, dtype=np.int16)
            if channels > 1:
                audio = audio.reshape(-1, channels)
            stream.write(audio)
```

**Node stream-to-file example:**

```javascript
import fs from "node:fs";

const response = await fetch("http://127.0.0.1:8765/v1/audio/speech", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.MERY_TOKEN}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    model: "tts-1",
    voice: "alloy",
    input: "Hello from Node streaming Mery",
    response_format: "pcm",
    stream: true,
  }),
});

if (!response.ok) {
  console.error(await response.text());
  process.exit(1);
}

console.log("PCM", response.headers.get("X-Mery-Sample-Rate"), response.headers.get("X-Mery-Channels"));
const file = fs.createWriteStream("speech.pcm");
await response.body.pipeTo(new WritableStream({
  write(chunk) {
    file.write(Buffer.from(chunk));
  },
  close() {
    file.end();
  },
}));
```

**Browser defer rationale:** Browser streaming playback needs a small helper to convert PCM chunks into scheduled Web Audio buffers. A naive snippet will stutter because chunk arrival timing and AudioContext scheduling are different problems.

```text
Do not publish browser playback docs until there is:
  - a PCM-to-AudioBuffer helper
  - buffering/scheduling strategy
  - test/demo page
  - cleanup/cancel behavior
```

**Files affected when implementing:**

| File | Change |
|---|---|
| `docs/integration/openai-streaming.md` | NEW — detailed streaming examples and raw PCM explanation |
| `docs/integration/openai-compat.md` | Link to streaming guide after P1 |
| `examples/openai_streaming/stream_pcm_httpx.py` | Python save-to-file example |
| `examples/openai_streaming/play_pcm_httpx.py` | Python sounddevice playback example |
| `examples/openai_streaming/stream_pcm_node.mjs` | Node stream-to-file example |
| `tests/examples/test_openai_streaming_examples.py` | Optional smoke/import checks for examples |

**Testing requirements:**

```text
1. Python save-to-file example can run against local test server/fake adapter
2. Python playback example imports cleanly; playback path can be marked manual if sounddevice device missing
3. Node example syntax/smoke tested if Node is available; otherwise documented manual example
4. Examples use local Mery token, not a real OpenAI key
5. Examples read sample rate/channels from headers, not hardcode 24000
6. Docs explain raw PCM is not a WAV file and how to convert if needed
```

**Recommendation nuance:** Examples are part of the feature for raw PCM streaming. Without them, the protocol may be correct but hard to use. Stage them so simple server-side consumers are supported first, while browser playback gets a proper helper instead of a fragile snippet.

---

## Q26 — Streaming implementation slice

**Verdict:** Use a **vertical streaming tracer bullet**. Do not start with a route-only hack, and do not build streaming primitives in isolation without proving the HTTP path. The first P1 slice should prove client-to-route-to-fake-adapter-to-client streaming end-to-end with metadata, ordering, cancellation, and error behavior.

**Recommended first slice:**

```text
Test client
  -> POST /v1/audio/speech { stream=true, response_format=pcm }
  -> OpenAISpeechRequest validates stream/format
  -> resolver/VoiceRegistry picks FakeStreamingAdapter
  -> FakeStreamingAdapter yields delayed PCMChunk sequence
  -> route derives headers from first PCMChunk
  -> StreamingResponse yields raw PCM bytes in order
  -> contract test asserts ordered chunks + headers + no buffering-all-first
```

**Options considered:**

| Option | Design | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Add `stream=true` route branch first | Fast | Easy to skip metadata/backpressure/cancel correctness | ❌ |
| B | Build streaming primitives first | Clean components | Does not prove HTTP/StreamingResponse behavior | ❌ |
| C | Vertical streaming tracer bullet | End-to-end proof while staying modular | More setup | ✅ P1 slice |

**Slice 1 — Fake streaming contract path:**

```text
Includes:
  - OpenAISpeechRequest.stream validation
  - PCMChunk metadata schema
  - PCMStreamMetadata helper
  - FakeStreamingAdapter yielding 3+ delayed chunks
  - /v1/audio/speech StreamingResponse branch for stream=true+pcm
  - content-type and X-Mery audio headers from first chunk
  - ordered chunk delivery contract test
  - unsupported stream=true+wav test

Excludes:
  - real Piper/Kokoro streaming verification
  - browser playback helper
  - mp3/opus/aac/flac
  - SSE/NDJSON/trailers
```

**Slice 2 — Cancellation/backpressure hardening:**

```text
Includes:
  - adapter.cancel(session_id) idempotency tests
  - client disconnect contract test
  - bounded queue helper / thread-backed runner pattern
  - backpressure timeout test
  - stream_cancelled and stream_backpressure_timeout logs
```

**Slice 3 — Error boundary behavior:**

```text
Includes:
  - failure before first chunk -> OpenAI JSON error
  - failure after first chunk -> terminate stream + structured log
  - metadata change mid-stream -> cancel + log audio_metadata_changed
```

**Slice 4 — Examples/docs:**

```text
Includes:
  - docs/integration/openai-streaming.md
  - Python httpx stream-to-file example
  - Python sounddevice playback helper example
  - Node stream-to-file example
```

**Slice 5 — Real-engine validation:**

```text
Includes:
  - Piper/Kokoro optional marked streaming tests if their adapters can stream chunks
  - if a real engine only produces full audio at first, adapter may yield one PCMChunk but still follows stream contract
  - no default CI dependency on real engine packages
```

**Why vertical tracer bullet wins:**

| Criterion | Why this wins |
|---|---|
| Flexible | Proves streaming API with fake adapter before binding to Piper/Kokoro behavior |
| Clean | Every new primitive is introduced because the route needs it, not speculative infrastructure |
| SoC | Request schema, route streaming, adapter chunks, audio metadata, and tests each own one seam |
| Modular | Fake adapter, Piper, Kokoro, and future engines share the same streaming route path |
| Standalone | First slice runs offline and in-memory; no engines, models, browser, or cloud needed |
| Scalable | Later providers plug into an already tested streaming contract |
| Well-tested | Each slice has explicit success criteria and does not rely on real-time/flaky audio playback |

**Concrete issue breakdown:**

```text
Issue 1: Add streaming request validation
  Done when stream=true+pcm accepted and stream=true+wav rejected in schema tests.

Issue 2: Add PCMChunk metadata + PCMStreamMetadata helper
  Done when metadata/header/stability unit tests pass.

Issue 3: Add FakeStreamingAdapter fixture
  Done when fake adapter yields deterministic delayed PCMChunk sequence.

Issue 4: Add StreamingResponse branch
  Done when contract test receives raw PCM chunks with headers from first chunk.

Issue 5: Add cancellation/backpressure tests
  Done when disconnect calls adapter.cancel and bounded queue timeout cancels producer.

Issue 6: Add streaming error boundary tests
  Done when before-first-byte JSON and after-first-byte termination behavior are tested.

Issue 7: Add docs/examples
  Done when Python/Node examples align with headers/schema and are smoke-tested or marked manual.
```

**Testing requirements for the first slice:**

```text
1. FakeStreamingAdapter yields at least 3 chunks with sequence 0,1,2
2. Test client receives chunks in exact order
3. Response headers match first chunk metadata
4. The route does not collect all chunks before returning the response
5. stream=true+wav returns unsupported_streaming_response_format before adapter starts
6. stream=false blocking behavior remains unchanged
7. No real engine/model/network/browser dependency in default tests
```

**Recommendation nuance:** This mirrors the P0 strategy: prove the end-to-end seam with fake components first, then harden lifecycle behavior, then validate real engines. It keeps P1 streaming useful without letting it become a pile of route-specific hacks.

---

## Q27 — P1 streaming definition of done

**Verdict:** P1 streaming is done when the **protocol path is complete and well-tested with fake streaming fixtures**, including chunks, headers, cancellation, backpressure, error behavior, and docs/examples. Real-engine streaming verification should be a release gate when feasible, but P1 should not be blocked on every real engine producing true incremental chunks.

Selected definition:

```text
P1 done = Option B
Release confidence = optional Option C gate when real engine fixtures are available
```

**Why not require real-engine chunk streaming as the core P1 definition:** Some TTS engines may internally generate a full waveform before returning audio. Their adapter can still conform by yielding one or more `PCMChunk`s, but the protocol feature should not depend on whether a specific engine is truly incremental internally. P1 is about the HTTP streaming contract and lifecycle correctness.

**Options considered:**

| Option | Design | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Fake contract only: `stream=true+pcm` returns chunks | Fast | Misses cancel/backpressure/error/docs completeness | ❌ |
| B | Fake contract + cancellation/backpressure/error/docs | Strong protocol definition; standalone and deterministic | Does not prove real engine behavior | ✅ P1 done |
| C | B + one real engine streaming/manual verification | Extra confidence | Real engines may not truly chunk; optional deps make CI flaky | ✅ release gate when feasible |
| D | Full parity: WAV/MP3/browser/all engines | Complete | Massive scope creep | ❌ |

**Precise P1 acceptance criteria:**

```text
Request/schema:
  - stream=true + response_format=pcm is accepted
  - stream=true + response_format=wav/mp3/opus/aac/flac is rejected before synthesis starts
  - stream=false behavior remains unchanged from P0

Streaming response:
  - response Content-Type is audio/L16 with rate/channels
  - X-Mery audio metadata headers are derived from first PCMChunk
  - fake adapter yields at least 3 chunks and client receives them in order
  - route does not buffer the full stream before responding

Lifecycle:
  - client disconnect calls adapter.cancel(session_id)
  - adapter.cancel is idempotent
  - bounded queue prevents unbounded memory growth
  - backpressure timeout cancels producer and logs structured event

Errors:
  - failures before first byte return OpenAI-shaped JSON errors
  - failures after first byte terminate stream and log structured event
  - metadata change mid-stream cancels and logs audio_metadata_changed

Docs/examples:
  - docs/integration/openai-streaming.md exists
  - Python httpx stream-to-file example exists
  - Python sounddevice playback helper example exists or is marked manual
  - Node stream-to-file example exists
```

**Optional real-engine release gate:**

```text
Before advertising P1 streaming as release-ready:
  - run at least one marked real-engine streaming/manual check if engine fixture is available
  - recommended: Piper-plus or Kokoro through the same /v1/audio/speech stream=true+pcm route
  - acceptable result: engine yields one valid PCMChunk or multiple chunks; route still streams correctly
  - failure mode: if engine package/model unavailable, default CI remains green and release notes state manual check status
```

**Why B + optional C satisfies the design constraints:**

| Criterion | Why this wins |
|---|---|
| Flexible | Protocol works regardless of whether engines are incremental or full-waveform internally |
| Clean | P1 done criteria are route/protocol lifecycle criteria, not provider-specific behavior |
| SoC | Fake fixtures prove protocol; marked engine tests prove adapter reality separately |
| Modular | Future engines plug into the same `AsyncIterator[PCMChunk]` contract without redefining P1 |
| Standalone | Default CI needs no real engine, model download, browser, OpenAI cloud, or audio device |
| Scalable | Provider count does not multiply the definition of done |
| Well-tested | The hard streaming behaviors are deterministic and covered by fake fixtures |

**Recommended test grouping:**

```text
tests/unit/audio/
  - PCMChunk metadata
  - PCMStreamMetadata stability
  - backpressure helper

tests/unit/openai_compat/
  - stream request validation
  - unsupported format errors

tests/contract/api/
  - streaming happy path with fake adapter
  - disconnect/cancel
  - pre-first-byte error
  - post-first-byte failure/log
  - metadata change
  - backpressure timeout

tests/engine/ (optional)
  - piper_plus_openai_streaming.py
  - kokoro_openai_streaming.py
```

**Files affected when implementing done criteria:**

| File | Change |
|---|---|
| `tests/contract/api/test_openai_speech_streaming.py` | Core streaming happy path and lifecycle tests |
| `tests/contract/api/test_openai_speech_streaming_errors.py` | Before/after first byte error behavior |
| `tests/unit/audio/test_backpressure.py` | Queue/full/timeout/no-drop tests |
| `tests/unit/audio/test_stream_metadata.py` | Header/stability/metadata-change tests |
| `docs/integration/openai-streaming.md` | User guide and examples |
| `examples/openai_streaming/*` | Python/Node examples |
| `tests/engine/test_*_openai_streaming.py` | Optional real-engine release checks |

**Recommendation nuance:** This keeps P1 honest: the streaming protocol is complete even if a first real engine only yields one chunk. True low-TTFB engine internals are a later engine-optimization question, not a reason to block the HTTP streaming contract.

---

## What's next (Q28+ candidates)

Potential next streaming branches:

1. **Cancellation semantics** — how to detect disconnect and call `adapter.cancel(session_id)` reliably.
2. **Chunk metadata source** — whether sample rate/channels live in `PCMChunk`, `VoiceDescriptor`, or adapter descriptor.
3. **Backpressure policy** — queue size, slow client handling, and synthesis thread cancellation.
4. **Streaming error behavior** — what happens if synthesis fails before vs. after first chunk.
5. **Client examples** — Python `httpx.stream()` and browser fetch streaming examples.

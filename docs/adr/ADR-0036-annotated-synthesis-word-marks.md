# ADR-0036 — Annotated Synthesis: Word-Level Speech Marks Protocol

**Status:** Proposed
**Date:** 2026-06-08
**Source:** Grilling session — word-level karaoke for Zam Reader reading experience

## Context

Zam Reader's TTS read-aloud feature highlights the current sentence while audio plays (sentence-level karaoke). Word-level karaoke — highlighting each word as it is spoken — requires the server to return word-level timing data alongside the synthesized audio.

The current architecture (`EngineAdapter.synthesize()` → `AsyncIterator[PCMChunk]`) returns only raw audio. There is no mechanism for engines to declare timing capability, no API surface to return marks, and no client-facing endpoint for annotated synthesis.

The underlying problem has two parts:

1. **Engine layer**: `EngineAdapter` has no concept of timing output. `KokoroAdapter` uses `kokoro_onnx`, which discards phoneme duration outputs from the ONNX session (`sess.run(None, inputs)[0]` — only the first output, audio, is retained). The `Kokoro-82M-v1.0-ONNX-timestamped` model exposes a second output (phoneme duration tensor) that the library ignores.

2. **API layer**: `POST /v1/audio/speech` is an OpenAI-compatible endpoint that returns binary audio only (`audio/wav` or raw PCM). Adding timing metadata to this response would break all existing clients.

Three approaches were considered and rejected before arriving at the design below:

- **Proportional estimation** (distribute audio duration by phoneme count): rejected because estimation-based timing drifts and breaks the reading experience. Mery must not return marks it cannot accurately compute.
- **PyTorch / `kokoro` native library**: has built-in timing but requires ~2GB PyTorch dependency, contradicting ADR-0004's CPU-only ONNX runtime commitment.
- **Subclass `kokoro_onnx.Kokoro`**: requires overriding `_create_audio()` (private method), violating Liskov substitution and coupling mery to library internals.

## Decision — Engine capability: `AnnotatedSynthesisCapable` Protocol

Engines that can produce accurate word-level timing in a single synthesis pass declare this by implementing a separate optional Protocol. `EngineAdapter` is not modified.

```python
# src/mery_tts/engines/marks.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from mery_tts.engines.base import PCMChunk
from mery_tts.voice import VoiceDescriptor


@dataclass(frozen=True, slots=True)
class SpeechMark:
    """Word-level timing mark produced during synthesis.

    `word` is the token as produced by the TTS engine (post-normalization).
    `start_ms` and `end_ms` are milliseconds from the start of the synthesized audio.
    No character offsets are included: mery does not know the client's text
    representation or encoding. Clients map word → position via sequential search.
    """
    word: str
    start_ms: int
    end_ms: int


@dataclass
class AnnotatedSynthesisResult:
    """Complete synthesis result with word timing.

    `chunks` uses the same PCMChunk type as EngineAdapter.synthesize() for
    consistency across the audio pipeline. Conversion to bytes (WAV/PCM)
    happens at the API boundary via the existing encoder layer.
    """
    chunks: list[PCMChunk]
    marks: list[SpeechMark]


@runtime_checkable
class AnnotatedSynthesisCapable(Protocol):
    """Optional engine capability: single-pass synthesis with word timing.

    Engines that implement this Protocol produce both audio and word-level
    speech marks in one synthesis call. Engines that do not implement it
    return audio only via EngineAdapter.synthesize().

    Callers check capability via isinstance(engine, AnnotatedSynthesisCapable)
    at synthesis time. The orchestrator handles the dispatch; adapters and
    route handlers never check this directly.

    Only implement when timing data is native to the synthesis pass (i.e.,
    the engine model produces duration outputs). Do not implement with
    estimation, post-hoc alignment, or proportional distribution.
    """

    async def synthesize_annotated(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AnnotatedSynthesisResult: ...
```

**Rationale for Protocol (not ABC extension):**
- Interface Segregation: engines that cannot produce timing (PiperPlus) are not forced to implement a no-op stub or raise `NotImplementedError`.
- Open/Closed: new engines opt in by implementing the Protocol; `EngineAdapter` is never modified.
- `@runtime_checkable` enables `isinstance` dispatch without nominal inheritance.

## Decision — Gap bridge: `TimedKokoroSession`

`kokoro_onnx` does not expose the duration tensor from `_create_audio()`. The `Kokoro-82M-v1.0-ONNX-timestamped` ONNX model exposes `outputs[1]` (phoneme durations) but the library discards it.

Rather than subclassing `kokoro_onnx.Kokoro` or calling `self.sess` via inherited state, `TimedKokoroSession` owns its own `onnxruntime.InferenceSession` initialized with the timestamped model file:

```python
# src/mery_tts/engines/kokoro/timed_session.py
#
# Gap bridge: exists because kokoro_onnx does not expose the duration tensor
# that the Kokoro-82M ONNX timestamped model produces. When kokoro_onnx adds
# native timing support, replace this class with a direct library call and
# delete this file.

from __future__ import annotations
import numpy as np
import onnxruntime as rt  # direct dep: kokoro-timed extra
from dataclasses import dataclass
from numpy.typing import NDArray
from mery_tts.engines.marks import SpeechMark

DURATION_UNITS_PER_SECOND = 80.0  # Kokoro model duration unit → seconds


@dataclass
class TimedAudioOutput:
    audio: NDArray[np.float32]
    sample_rate_hz: int
    marks: list[SpeechMark]


class TimedKokoroSession:
    """Composition wrapper over onnxruntime for timestamped Kokoro model.

    Does NOT subclass or access kokoro_onnx.Kokoro internals. Owns its own
    InferenceSession initialized with the timestamped model variant.
    Tokenizer is injected (from the standard KokoroAdapter runtime) to avoid
    duplicate espeak-ng initialization.
    """

    def __init__(
        self,
        model_path: str,
        voices_path: str,
        tokenizer: object,  # kokoro_onnx.Tokenizer — injected
        sample_rate_hz: int = 24_000,
    ) -> None:
        self._sess = rt.InferenceSession(
            model_path, providers=["CPUExecutionProvider"]
        )
        self._voices: NDArray[np.float32] = np.load(voices_path)
        self._tokenizer = tokenizer
        self._sample_rate_hz = sample_rate_hz

    def synthesize(
        self,
        text: str,
        voice_name: str,
        speed: float = 1.0,
        lang: str = "en-us",
    ) -> TimedAudioOutput:
        phonemes: str = self._tokenizer.phonemize(text, lang)
        tokens = self._tokenizer.tokenize(phonemes)

        voice_style = self._voices[voice_name]
        padded = [[0, *tokens, 0]]

        inputs = self._build_inputs(padded, voice_style, speed)
        outputs = self._sess.run(None, inputs)

        audio: NDArray[np.float32] = outputs[0]
        # outputs[1] = phoneme duration tensor (only present in timestamped model)
        durations: NDArray[np.float32] | None = (
            outputs[1] if len(outputs) > 1 else None
        )

        marks = self._build_marks(phonemes, tokens, durations) if durations is not None else []
        return TimedAudioOutput(audio=audio, sample_rate_hz=self._sample_rate_hz, marks=marks)

    def _build_inputs(
        self,
        tokens: list[list[int]],
        voice_style: NDArray[np.float32],
        speed: float,
    ) -> dict[str, object]:
        input_names = {i.name for i in self._sess.get_inputs()}
        if "input_ids" in input_names:
            return {
                "input_ids": tokens,
                "style": np.array(voice_style, dtype=np.float32),
                "speed": np.array([speed], dtype=np.int32),
            }
        return {
            "tokens": tokens,
            "style": voice_style,
            "speed": np.ones(1, dtype=np.float32) * speed,
        }

    def _build_marks(
        self,
        phonemes: str,
        tokens: list[int],
        durations: NDArray[np.float32],
    ) -> list[SpeechMark]:
        """Map per-phoneme durations to word-level SpeechMarks.

        espeak-ng preserves word boundaries as spaces in the phoneme string.
        Each character in the filtered phoneme string (matching a token in vocab)
        corresponds to one duration entry. Spaces mark word boundaries.
        """
        # Rebuild per-character duration assignment (skip pad tokens at index 0 and -1)
        # durations shape: (1, seq_len) or (seq_len,)
        flat_durations = np.asarray(durations).flatten()
        # Remove padding tokens from duration array if present
        dur_slice = flat_durations[1 : 1 + len(tokens)]

        marks: list[SpeechMark] = []
        cursor_s = 0.0
        token_idx = 0

        for word_phonemes in phonemes.split(" "):
            if not word_phonemes:
                continue
            word_tokens = self._tokenizer.tokenize(word_phonemes)
            n = len(word_tokens)
            if token_idx + n > len(dur_slice):
                break

            word_dur_s = float(np.sum(dur_slice[token_idx : token_idx + n])) / DURATION_UNITS_PER_SECOND
            start_ms = int(cursor_s * 1000)
            end_ms = int((cursor_s + word_dur_s) * 1000)

            # Recover surface word from phoneme string back-mapping is not
            # possible here; use phoneme string segment as proxy.
            # KokoroAdapter post-processes this with original word list.
            marks.append(SpeechMark(word=word_phonemes, start_ms=start_ms, end_ms=end_ms))

            cursor_s += word_dur_s
            token_idx += n

        return marks
```

`onnxruntime` is added as a **direct** dependency under the `kokoro-timed` optional extra:

```toml
# pyproject.toml
[project.optional-dependencies]
kokoro-timed = ["kokoro-onnx>=0.4", "onnxruntime>=1.16"]
```

**`KokoroAdapter` implements `AnnotatedSynthesisCapable`** when a `TimedKokoroSession` is injected at construction. The injection is optional; without it, `KokoroAdapter` is a plain `EngineAdapter` with no timing support.

## Decision — Synthesis dispatch: `SynthesisOrchestrator`

A standalone function (not a class — no shared state to justify a class) handles dispatch. Route handlers and API layers call this and never check `isinstance` directly:

```python
# src/mery_tts/engines/orchestrator.py

async def run_synthesis(
    engine: EngineAdapter,
    text: str,
    voice: VoiceDescriptor,
    *,
    want_marks: bool = False,
    request_id: str | None = None,
) -> AnnotatedSynthesisResult:
    if want_marks and isinstance(engine, AnnotatedSynthesisCapable):
        return await engine.synthesize_annotated(text, voice, request_id=request_id)
    chunks = [c async for c in engine.synthesize(text, voice, request_id=request_id)]
    return AnnotatedSynthesisResult(chunks=chunks, marks=[])
```

Empty `marks=[]` is an **honest signal** — the engine does not support timing. Callers degrade gracefully (sentence-level highlighting).

## Decision — Voice capabilities in API schema

`VoiceSummary` gains a `capabilities` field:

```python
# src/mery_tts/schemas/v1.py

class VoiceCapabilities(BaseModel):
    model_config = ConfigDict(frozen=True)
    word_marks: bool = False
    # Future: phoneme_marks, sentence_marks, streaming_marks, etc.

class VoiceSummary(BaseModel):
    model_config = ConfigDict(frozen=True)
    voice_id: str
    engine_id: str
    display_name: str
    streaming: StreamingCapabilityInfoVo | None = None
    capabilities: VoiceCapabilities = Field(default_factory=VoiceCapabilities)
```

`capabilities.word_marks` is `True` for voices resolved to a `KokoroAdapter` with a `TimedKokoroSession`, `False` for all others. The voice resolver sets this during `GET /v1/voices/installed` response construction.

## Decision — New endpoint: `/v1/audio/speech/annotated`

`POST /v1/audio/speech` is an OpenAI-compatible endpoint and returns binary audio only. This contract is immutable.

A new Mery-native endpoint returns JSON with embedded audio and marks:

```
POST /v1/audio/speech/annotated
Authorization: Bearer <token>
Content-Type: application/json

{
  "voice": "kokoro.en-us.af_heart",
  "input": "Hello world",
  "response_format": "wav",
  "speed": 1.0
}

→ 200 OK
Content-Type: application/json

{
  "audio_b64": "<base64-encoded WAV>",
  "sample_rate_hz": 24000,
  "duration_ms": 820,
  "marks": [
    {"word": "Hello", "start_ms": 0,   "end_ms": 320},
    {"word": "world", "start_ms": 340, "end_ms": 680}
  ],
  "marks_available": true
}
```

If the resolved voice does not support marks (`capabilities.word_marks = false`), the endpoint returns `marks: [], marks_available: false` with HTTP 200. It does NOT return 4xx — the client declared a preference, not a requirement.

The endpoint reuses the same auth middleware, voice resolution, and `SynthesisOrchestrator` as `/v1/audio/speech`. It does not duplicate synthesis logic.

## Alternatives rejected

| Alternative | Reason rejected |
|---|---|
| Proportional phoneme-count estimation | Estimation drifts; ADR-0008 (zreader) explicitly rejects estimation-based timing |
| `kokoro` native (PyTorch) | ~2GB dep; contradicts ADR-0004 CPU-only ONNX runtime decision |
| Subclass `kokoro_onnx.Kokoro`, override `_create_audio` | Overrides private method (`_` prefix), violates LSP, couples mery to library internals |
| Extend `EngineAdapter` with `synthesize_with_marks()` | ISP violation — forces all engines to see/stub a method they cannot implement |
| Add marks to existing `/v1/audio/speech` response | Breaking change to binary-only OpenAI-compatible endpoint |
| Engine-agnostic forced aligner (`aeneas`, `stable-ts`) | Heavy deps (ffmpeg, torch); adds post-hoc synthesis latency; overkill for sentence-level TTS |

## Consequences

**Enables:**
- Zam Reader word-level karaoke when Kokoro timestamped voices are installed
- Any future engine can opt into accurate timing by implementing `AnnotatedSynthesisCapable`
- `GET /v1/voices/installed` tells clients which voices support marks — no probing required
- `TimedKokoroSession` is a contained, deletable gap bridge when `kokoro_onnx` adds native timing

**Constrains:**
- Word marks are only available for Kokoro voices installed from the `kokoro-timed` extra with the timestamped model variant — users must install this variant explicitly
- Piper voices never return marks (`VoiceCapabilities.word_marks = False`) — this is honest, not a limitation to hide
- `/v1/audio/speech/annotated` adds a Mery-native path that non-Mery clients (pure OpenAI-compatible consumers) do not use
- `TimedKokoroSession._build_marks()` uses space-delimited phoneme string word boundaries — this is accurate for English but may miscount for languages where espeak-ng uses different word separators

## Related

- ADR-0004 (engine strategy — dual engine, ONNX-only)
- ADR-0012 (audio delivery mode)
- ADR-0014 (OpenAI-compatible speech layer)
- ADR-0019 (provider adapter taxonomy)
- ADR-0035 (streaming capability and provider scope)
- `src/mery_tts/engines/marks.py`
- `src/mery_tts/engines/kokoro/timed_session.py`
- `src/mery_tts/engines/orchestrator.py`
- zreader ADR-0037 (consumer side of this protocol)

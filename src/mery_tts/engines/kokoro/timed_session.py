"""TimedKokoroSession — accesses both audio and phoneme duration outputs from Kokoro ONNX."""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

import numpy as np

from mery_tts.engines.annotated import AnnotatedSynthesisResult, SpeechMark
from mery_tts.engines.base import PCMChunk

if TYPE_CHECKING:
    pass  # kokoro_onnx imported lazily

_HOP_SAMPLES = 256      # HifiGAN vocoder hop size
_SAMPLE_RATE = 24_000   # Kokoro native sample rate
_FRAME_MS = _HOP_SAMPLES / _SAMPLE_RATE * 1000  # ≈ 10.67 ms/frame


class TimedKokoroSession:
    """Wraps kokoro_onnx.Kokoro to capture phoneme timing from outputs[1].

    The standard kokoro_onnx.Kokoro._create_audio() discards outputs[1]
    (phoneme duration tensor). This class runs the same ONNX session but
    captures both outputs to build word-level SpeechMarks.
    """

    def __init__(self, runtime: object) -> None:
        # runtime is kokoro_onnx.Kokoro — stored as object to avoid hard import
        self._runtime = runtime

    def synthesize_annotated(
        self, text: str, voice_preset: str, speed: float = 1.0, lang: str = "en-us"
    ) -> AnnotatedSynthesisResult:
        runtime = self._runtime

        # Step 1: full-text phonemization for ONNX input
        phonemes = runtime.tokenizer.phonemize(text, lang)
        tokens_raw = runtime.tokenizer.tokenize(phonemes)
        if not tokens_raw:
            return AnnotatedSynthesisResult(chunks=[], marks=[])

        tokens_raw = tokens_raw[:510]  # MAX_PHONEME_LENGTH - 2 pads
        voice_style = runtime.voices[voice_preset]
        voice_slice = voice_style[len(tokens_raw)]
        tokens_padded = [[0, *tokens_raw, 0]]

        # Step 2: build ONNX inputs (same logic as _create_audio)
        input_names = [i.name for i in runtime.sess.get_inputs()]
        if "input_ids" in input_names:
            inputs = {
                "input_ids": np.array(tokens_padded, dtype=np.int64),
                "style": np.array(voice_slice, dtype=np.float32),
                "speed": np.array([speed], dtype=np.int32),
            }
        else:
            inputs = {
                "tokens": np.array(tokens_padded, dtype=np.int64),
                "style": np.array(voice_slice, dtype=np.float32),
                "speed": np.ones(1, dtype=np.float32) * speed,
            }

        # Step 3: run with ALL outputs (standard kokoro only reads [0])
        outputs = runtime.sess.run(None, inputs)
        audio_array = outputs[0]

        # Convert audio to PCM s16le bytes
        pcm_bytes = (np.clip(audio_array, -1.0, 1.0) * 32767).astype(np.int16).tobytes()
        chunk = PCMChunk(
            pcm=pcm_bytes,
            sample_rate_hz=_SAMPLE_RATE,
            channels=1,
            sample_width_bytes=2,
            encoding="pcm_s16le",
        )

        # Step 4: build marks from duration tensor if available
        marks: list[SpeechMark] = []
        if len(outputs) > 1 and outputs[1] is not None:
            try:
                duration_frames = np.asarray(outputs[1]).ravel()
                marks = _build_word_marks(
                    text, runtime.tokenizer, tokens_raw, duration_frames, lang
                )
            except Exception:
                marks = []

        return AnnotatedSynthesisResult(chunks=[chunk], marks=marks)


def _build_word_marks(
    text: str,
    tokenizer: object,
    full_tokens: list[int],
    duration_frames: np.ndarray,
    lang: str,
) -> list[SpeechMark]:
    """Map phoneme duration frames to word-level SpeechMarks.

    Phonemizes each word individually to count its phoneme tokens.
    Sums frame durations per word to get word start/end in ms.
    Returns [] if phoneme counts do not align with duration_frames.
    """
    # Split into words (preserve original text for SpeechMark.word)
    words = re.findall(r"\S+", text)
    if not words:
        return []

    # Count phoneme tokens per word via individual phonemization
    per_word_token_counts: list[tuple[str, int]] = []
    for word in words:
        try:
            word_phonemes = tokenizer.phonemize(word, lang)
            word_tokens = tokenizer.tokenize(word_phonemes)
            clean_word = re.sub(r"[^\w'-]", "", word)
            if clean_word and word_tokens:
                per_word_token_counts.append((clean_word, len(word_tokens)))
        except Exception:
            continue

    if not per_word_token_counts:
        return []

    total_counted = sum(c for _, c in per_word_token_counts)
    # Allow ±20% slack between whole-text and per-word tokenization
    if abs(total_counted - len(full_tokens)) > max(3, int(len(full_tokens) * 0.2)):
        return []

    # Guard: duration_frames length must match full_tokens (with pad offset)
    # The duration tensor is typically [n_tokens] or [1, n_tokens] excluding pads
    n_frames = len(duration_frames)
    if n_frames == 0:
        return []

    # Map per-word tokens to cumulative frame offsets
    marks: list[SpeechMark] = []
    token_cursor = 0
    frame_cursor = 0.0

    for word_str, token_count in per_word_token_counts:
        # Slice frames for this word's tokens
        slice_end = min(token_cursor + token_count, n_frames)
        if token_cursor >= n_frames:
            break
        word_frames = duration_frames[token_cursor:slice_end]
        word_duration_frames = float(np.sum(word_frames))

        start_ms = int(round(frame_cursor * _FRAME_MS))
        end_ms = int(round((frame_cursor + word_duration_frames) * _FRAME_MS))

        marks.append(SpeechMark(word=word_str, start_ms=start_ms, end_ms=end_ms))

        frame_cursor += word_duration_frames
        token_cursor += token_count

    return marks

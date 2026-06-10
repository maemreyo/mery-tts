"""PiperTimedSession — word-level timing marks via proportional phoneme distribution.

The lessac-low (and most V1 piper) ONNX models expose only a single audio
output, no duration tensor.  We therefore fall back to phoneme-proportional
timing: the synthesized audio duration is split across words in proportion to
each word's share of the total phoneme count.  piper-tts returns a space
character `' '` as word boundary in the phoneme list, which lets us group
phonemes per word without re-running the phonemizer.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from mery_tts.engines.annotated import AnnotatedSynthesisResult, SpeechMark
from mery_tts.engines.base import PCMChunk

if TYPE_CHECKING:
    pass  # piper imported lazily


class PiperTimedSession:
    """Wraps a ``piper.PiperVoice`` to produce word-timed AnnotatedSynthesisResult.

    Strategy:
    1. Synthesize normally — collect PCM chunks and the phoneme list each chunk
       carries.  piper-tts always provides per-chunk phoneme lists.
    2. Split the aggregate phoneme list by space characters (word boundaries).
    3. Distribute the total audio duration proportionally across phoneme groups.
    4. Map groups back to original text words.
    """

    def __init__(self, runtime: object, *, sample_rate: int) -> None:
        self._runtime = runtime
        self._sample_rate = sample_rate

    def synthesize_annotated(self, text: str) -> AnnotatedSynthesisResult:
        all_phonemes: list[str] = []
        all_pcm: list[bytes] = []

        for chunk in self._runtime.synthesize(text):  # type: ignore[union-attr]
            all_pcm.append(chunk.audio_int16_bytes)
            all_phonemes.extend(chunk.phonemes)

        pcm_bytes = b"".join(all_pcm)
        pcm_chunk = PCMChunk(
            pcm=pcm_bytes,
            sample_rate_hz=self._sample_rate,
            channels=1,
            sample_width_bytes=2,
            encoding="pcm_s16le",
        )

        total_samples = len(pcm_bytes) // 2
        marks = _build_word_marks(text, all_phonemes, total_samples, self._sample_rate)
        return AnnotatedSynthesisResult(chunks=[pcm_chunk], marks=marks)


def _build_word_marks(
    text: str,
    phonemes: list[str],
    total_samples: int,
    sample_rate: int,
) -> list[SpeechMark]:
    """Map phoneme groups to word-level SpeechMarks via proportional timing."""
    if total_samples <= 0 or not phonemes:
        return []

    total_ms = int(total_samples / sample_rate * 1000)

    # Split phonemes into per-word groups using space as word boundary
    word_phoneme_groups: list[list[str]] = []
    current: list[str] = []
    for p in phonemes:
        if p == " ":
            if current:
                word_phoneme_groups.append(current)
                current = []
        else:
            current.append(p)
    if current:
        word_phoneme_groups.append(current)

    if not word_phoneme_groups:
        return []

    # Original text words (whitespace-split, strip punctuation for display)
    raw_words = text.split()
    n = min(len(raw_words), len(word_phoneme_groups))
    if n == 0:
        return []

    total_phonemes = sum(len(g) for g in word_phoneme_groups[:n])
    if total_phonemes == 0:
        return []

    marks: list[SpeechMark] = []
    cursor_ms = 0
    for i in range(n):
        group_len = len(word_phoneme_groups[i])
        word_ms = int(group_len / total_phonemes * total_ms)
        clean = re.sub(r"[^\w'-]", "", raw_words[i])
        if clean:
            marks.append(SpeechMark(
                word=clean,
                start_ms=cursor_ms,
                end_ms=cursor_ms + word_ms,
            ))
        cursor_ms += word_ms

    return marks

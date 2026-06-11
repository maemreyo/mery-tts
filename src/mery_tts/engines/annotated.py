"""AnnotatedSynthesisCapable Protocol and result types for word-timed synthesis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from mery_tts.engines.base import PCMChunk
from mery_tts.voice.descriptor import VoiceDescriptor


@dataclass(frozen=True, slots=True)
class SpeechMark:
    word: str
    start_ms: int
    end_ms: int


@dataclass(frozen=True, slots=True)
class AnnotatedSynthesisResult:
    chunks: list[PCMChunk]
    marks: list[SpeechMark] = field(default_factory=list)


@runtime_checkable
class AnnotatedSynthesisCapable(Protocol):
    """Optional engine capability: synthesize with word-level timing marks.

    Engines that support this return AnnotatedSynthesisResult from
    synthesize_annotated(). Callers should check isinstance(adapter, AnnotatedSynthesisCapable)
    before calling.
    """

    async def synthesize_annotated(
        self,
        text: str,
        voice: VoiceDescriptor,
    ) -> AnnotatedSynthesisResult: ...

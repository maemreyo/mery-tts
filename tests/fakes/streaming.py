"""Deterministic streaming test fakes.

ADR-0031: fakes live under ``tests/fakes/streaming.py`` — never in the
production package. These helpers are reusable across unit, contract, and
integration tests.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import ClassVar

from mery_tts.engines.base import EngineAdapter, PCMChunk
from mery_tts.streaming.cancellation import StreamCancellation
from mery_tts.streaming.config import StreamingConfig
from mery_tts.streaming.pipeline import StreamingPipeline
from mery_tts.voice.descriptor import VoiceDescriptor


class FakeStreamingAdapter(EngineAdapter):
    """Engine adapter that yields a deterministic multi-chunk PCM stream.

    Sequence numbers are left at the default (``0``) so the streaming
    pipeline can assign transport sequence numbers — that is the
    typical migration path for existing adapters.
    """

    engine_id: ClassVar[str] = "fake-streaming"
    accepted_voice_kinds: ClassVar[frozenset[str]] = frozenset({"preset"})

    def __init__(
        self,
        *,
        sample_rate_hz: int = 24_000,
        channels: int = 1,
        chunk_count: int = 3,
        chunk_size_bytes: int = 8,
        cancelled_request_ids: set[str] | None = None,
        cancel_after: int | None = None,
    ) -> None:
        self._sample_rate_hz = sample_rate_hz
        self._channels = channels
        self._chunk_count = chunk_count
        self._chunk_size_bytes = chunk_size_bytes
        self._cancelled_request_ids = cancelled_request_ids or set()
        self._cancel_after = cancel_after
        self.cancel_call_count = 0

    def health(self) -> str:
        return "available"

    def cancel(self, request_id: str) -> None:
        self.cancel_call_count += 1
        self._cancelled_request_ids.add(request_id)

    async def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)
        for index in range(self._chunk_count):
            if request_id is not None and request_id in self._cancelled_request_ids:
                break
            if self._cancel_after is not None and index >= self._cancel_after:
                break
            yield PCMChunk(
                pcm=f"chunk-{index}:{text}".encode().ljust(self._chunk_size_bytes, b"\x00"),
                sample_rate_hz=self._sample_rate_hz,
                channels=self._channels,
            )


class UnstableMetadataStreamingAdapter(EngineAdapter):
    """Adapter that emits metadata drift after the first chunk."""

    engine_id: ClassVar[str] = "fake-unstable"
    accepted_voice_kinds: ClassVar[frozenset[str]] = frozenset({"preset"})

    def __init__(self) -> None:
        self.cancel_call_count = 0

    def cancel(self, request_id: str) -> None:
        self.cancel_call_count += 1

    async def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)
        yield PCMChunk(pcm=b"first", sample_rate_hz=24_000, channels=1)
        yield PCMChunk(pcm=b"second", sample_rate_hz=48_000, channels=1)


class SlowStreamingAdapter(EngineAdapter):
    """Adapter that sleeps between chunks. Used for backpressure tests."""

    engine_id: ClassVar[str] = "fake-slow"
    accepted_voice_kinds: ClassVar[frozenset[str]] = frozenset({"preset"})

    def __init__(self, *, delay_seconds: float = 0.01, chunk_count: int = 4) -> None:
        self._delay_seconds = delay_seconds
        self._chunk_count = chunk_count
        self.cancel_call_count = 0

    def cancel(self, request_id: str) -> None:
        self.cancel_call_count += 1

    async def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)
        for index in range(self._chunk_count):
            await asyncio.sleep(self._delay_seconds)
            yield PCMChunk(
                pcm=f"slow-{index}:{text}".encode(),
                sample_rate_hz=24_000,
                channels=1,
            )


def fake_preset_voice() -> VoiceDescriptor:
    return VoiceDescriptor(
        voice_id="voice.fake.streaming",
        engine_id=FakeStreamingAdapter.engine_id,
        payload=__import__("mery_tts.voice", fromlist=["PresetVoicePayload"]).PresetVoicePayload(
            preset_id="fake-streaming"
        ),
    )


def build_pipeline(
    *,
    adapter: EngineAdapter | None = None,
    request_id: str = "req-test",
    config: StreamingConfig | None = None,
) -> StreamingPipeline:
    return StreamingPipeline(
        adapter=adapter or FakeStreamingAdapter(),
        voice=fake_preset_voice(),
        text="hello",
        request_id=request_id,
        config=config,
    )


def fake_cancellation(request_id: str = "req-test") -> StreamCancellation:
    return StreamCancellation(request_id=request_id)

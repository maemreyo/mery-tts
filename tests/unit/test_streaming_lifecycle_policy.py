from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from mery_tts.engines.base import EngineAdapter, PCMChunk
from mery_tts.streaming.pipeline import StreamingPipeline
from mery_tts.streaming.transports.http import build_openai_pcm_stream_response
from mery_tts.voice import PresetVoicePayload, VoiceDescriptor


class TwoChunkAdapter(EngineAdapter):
    engine_id = "fake"
    accepted_voice_kinds = frozenset({"preset"})

    def __init__(self) -> None:
        self.cancelled_request_id: str | None = None

    def cancel(self, request_id: str) -> None:
        self.cancelled_request_id = request_id

    async def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)
        yield PCMChunk(pcm=b"first", sample_rate_hz=24_000, channels=1)
        yield PCMChunk(pcm=b"second", sample_rate_hz=24_000, channels=1)


class DriftingAfterFirstByteAdapter(TwoChunkAdapter):
    async def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)
        yield PCMChunk(pcm=b"first", sample_rate_hz=24_000, channels=1)
        yield PCMChunk(pcm=b"drift", sample_rate_hz=48_000, channels=1)


def voice() -> VoiceDescriptor:
    return VoiceDescriptor(
        voice_id="voice.fake",
        engine_id="fake",
        payload=PresetVoicePayload(preset_id="fake"),
    )


@pytest.mark.asyncio
async def test_streaming_pipeline_records_client_disconnect_cancellation() -> None:
    adapter = TwoChunkAdapter()
    pipeline = StreamingPipeline(
        adapter=adapter,
        voice=voice(),
        text="hello",
        request_id="req-stream-cancel",
    )
    stream = pipeline.run()

    first = await stream.__anext__()
    pipeline.cancel(reason="client_disconnect")
    with pytest.raises(StopAsyncIteration):
        await stream.__anext__()

    diagnostics = pipeline.lifecycle_diagnostics()
    assert first.pcm == b"first"
    assert diagnostics == {
        "cancelled": True,
        "cancelled_by": "client_disconnect",
        "phase": "post_first_byte",
    }
    assert adapter.cancelled_request_id == "req-stream-cancel"


@pytest.mark.asyncio
async def test_http_stream_post_first_byte_metadata_failure_records_structured_lifecycle() -> None:
    adapter = DriftingAfterFirstByteAdapter()
    pipeline = StreamingPipeline(
        adapter=adapter,
        voice=voice(),
        text="hello",
        request_id="req-stream-drift",
    )
    byte_stream, headers = await build_openai_pcm_stream_response(
        pipeline=pipeline,
        config=pipeline.config,
    )

    chunks = [chunk async for chunk in byte_stream]

    assert headers.extra["X-Mery-Request-Id"] == "req-stream-drift"
    assert chunks == [b"first"]
    assert pipeline.lifecycle_diagnostics() == {
        "cancelled": True,
        "cancelled_by": "post_first_byte_failure",
        "phase": "post_first_byte",
        "reason": "incompatible_chunk_metadata",
    }
    assert adapter.cancelled_request_id == "req-stream-drift"

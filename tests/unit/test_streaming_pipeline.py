"""Tests for the streaming pipeline orchestration."""

from __future__ import annotations

import pytest
from fakes.streaming import (
    FakeStreamingAdapter,
    UnstableMetadataStreamingAdapter,
    build_pipeline,
    fake_preset_voice,
)

from mery_tts.streaming.cancellation import StreamCancellation
from mery_tts.streaming.config import StreamingConfig
from mery_tts.streaming.metadata import StreamMetadataError
from mery_tts.streaming.pipeline import StreamingPipeline
from mery_tts.voice import VoiceDescriptor


@pytest.mark.asyncio
async def test_pipeline_yields_deterministic_chunks_with_transport_sequence() -> None:
    adapter = FakeStreamingAdapter(chunk_count=3)
    pipeline = build_pipeline(adapter=adapter, request_id="req-1")

    chunks = [chunk async for chunk in pipeline.run()]

    assert len(chunks) == 3
    assert [chunk.sequence for chunk in chunks] == [0, 1, 2]
    assert all(chunk.sample_rate_hz == 24_000 for chunk in chunks)


@pytest.mark.asyncio
async def test_pipeline_assigns_metadata_from_first_chunk() -> None:
    pipeline = build_pipeline()
    async for _ in pipeline.run():
        pass
    assert pipeline.metadata is not None
    assert pipeline.metadata.sample_rate_hz == 24_000
    assert pipeline.metadata.channels == 1
    assert pipeline.metadata.encoding == "pcm_s16le"


@pytest.mark.asyncio
async def test_pipeline_raises_on_post_start_metadata_drift() -> None:
    adapter = UnstableMetadataStreamingAdapter()
    pipeline = StreamingPipeline(
        adapter=adapter,
        voice=VoiceDescriptor(
            voice_id="voice.fake.unstable",
            engine_id=UnstableMetadataStreamingAdapter.engine_id,
            payload=__import__(
                "mery_tts.voice", fromlist=["PresetVoicePayload"]
            ).PresetVoicePayload(preset_id="fake-unstable"),
        ),
        text="hello",
        request_id="req-drift",
    )

    with pytest.raises(StreamMetadataError, match="unstable PCM metadata"):
        async for _ in pipeline.run():
            pass


@pytest.mark.asyncio
async def test_pipeline_cancellation_propagates_to_adapter() -> None:
    adapter = FakeStreamingAdapter(chunk_count=5)
    pipeline = build_pipeline(adapter=adapter, request_id="req-cancel")

    async def consume() -> None:
        async for _ in pipeline.run():
            pipeline.cancel()

    await consume()

    assert adapter.cancel_call_count >= 1
    assert pipeline.cancellation.is_cancelled()


@pytest.mark.asyncio
async def test_pipeline_cancel_is_idempotent() -> None:
    adapter = FakeStreamingAdapter(chunk_count=1)
    pipeline = build_pipeline(adapter=adapter, request_id="req-idem")

    pipeline.cancel()
    pipeline.cancel()
    pipeline.cancel()

    assert pipeline.cancellation.is_cancelled()
    assert adapter.cancel_call_count == 1


def test_stream_cancellation_exposes_request_id_and_event() -> None:
    cancellation = StreamCancellation(request_id="req-x")
    assert cancellation.request_id == "req-x"
    assert not cancellation.is_cancelled()
    cancellation.cancel()
    assert cancellation.is_cancelled()


@pytest.mark.asyncio
async def test_pipeline_consumes_single_chunk_provider_correctly() -> None:
    # ADR-0035/02: the route must work when an adapter yields a single
    # chunk. P1 streaming is not dependent on true incremental synthesis.

    class SingleChunkAdapter(FakeStreamingAdapter):
        def __init__(self) -> None:
            super().__init__(chunk_count=1)

    adapter = SingleChunkAdapter()
    pipeline = StreamingPipeline(
        adapter=adapter,
        voice=fake_preset_voice(),
        text="hi",
        request_id="req-single",
    )

    chunks = [chunk async for chunk in pipeline.run()]

    assert len(chunks) == 1
    assert chunks[0].sequence == 0


@pytest.mark.asyncio
async def test_pipeline_uses_config_first_chunk_timeout() -> None:
    config = StreamingConfig(first_chunk_timeout_seconds=0.001)
    pipeline = build_pipeline(config=config)
    # Just check the config is plumbed through. Actually triggering
    # the timeout requires a slow adapter, which is exercised in
    # integration. Here we just ensure the attribute is set.
    assert pipeline.config.first_chunk_timeout_seconds == 0.001

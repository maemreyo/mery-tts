"""HTTP transport for the OpenAI-compatible raw PCM stream.

ADR-0034: pre-first-byte errors are JSON; post-first-byte failures
terminate and log without JSON wrappers. ``audio/L16`` content type is
derived from the first chunk's metadata.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass

from mery_tts.engines.base import PCMChunk
from mery_tts.streaming.config import StreamingConfig
from mery_tts.streaming.metadata import (
    PCMStreamMetadata,
    StreamMetadataError,
    assert_http_encoding,
    derive_stream_metadata,
)
from mery_tts.streaming.pipeline import StreamingPipeline

MERY_DIAGNOSTIC_HEADER_NAMES = (
    "X-Mery-Request-Id",
    "X-Mery-Audio-Encoding",
    "X-Mery-Sample-Rate",
    "X-Mery-Channels",
    "X-Mery-Sample-Width-Bytes",
    "X-Mery-Stream-Format",
    "X-Accel-Buffering",
    "Cache-Control",
)


@dataclass(frozen=True, slots=True)
class HttpStreamHeaders:
    content_type: str
    extra: dict[str, str]


def build_audio_l16_content_type(metadata: PCMStreamMetadata) -> str:
    return f"audio/L16;rate={metadata.sample_rate_hz};channels={metadata.channels}"


def build_mery_diagnostic_headers(
    *,
    request_id: str,
    metadata: PCMStreamMetadata,
) -> dict[str, str]:
    return {
        "X-Mery-Request-Id": request_id,
        "X-Mery-Audio-Encoding": metadata.encoding,
        "X-Mery-Sample-Rate": str(metadata.sample_rate_hz),
        "X-Mery-Channels": str(metadata.channels),
        "X-Mery-Sample-Width-Bytes": str(metadata.sample_width_bytes),
        "X-Mery-Stream-Format": "raw-pcm",
        "X-Accel-Buffering": "no",
        "Cache-Control": "no-store",
    }


@dataclass(slots=True)
class _FirstChunk:
    chunk: PCMChunk
    iterator: AsyncIterator[PCMChunk]


async def _consume_first_chunk(
    pipeline: StreamingPipeline,
    *,
    timeout_seconds: float,
) -> _FirstChunk:
    iterator = pipeline.run()
    try:
        first = await asyncio.wait_for(iterator.__anext__(), timeout=timeout_seconds)
    except (TimeoutError, StopAsyncIteration) as exc:
        raise StreamMetadataError("adapter yielded no first chunk") from exc
    return _FirstChunk(chunk=first, iterator=iterator)


async def build_openai_pcm_stream_response(
    *,
    pipeline: StreamingPipeline,
    config: StreamingConfig,
) -> tuple[AsyncIterator[bytes], HttpStreamHeaders]:
    first_chunk_box = await _consume_first_chunk(
        pipeline, timeout_seconds=config.first_chunk_timeout_seconds
    )
    metadata = derive_stream_metadata(first_chunk_box.chunk)
    assert_http_encoding(first_chunk_box.chunk)

    content_type = build_audio_l16_content_type(metadata)
    headers_dict = build_mery_diagnostic_headers(request_id=pipeline.request_id, metadata=metadata)

    async def byte_stream() -> AsyncIterator[bytes]:
        try:
            yield first_chunk_box.chunk.pcm
            async for chunk in first_chunk_box.iterator:
                if pipeline.cancellation.is_cancelled():
                    break
                if not metadata.is_compatible(chunk):
                    break
                yield chunk.pcm
        finally:
            pipeline.cancel()

    return byte_stream(), HttpStreamHeaders(content_type=content_type, extra=headers_dict)

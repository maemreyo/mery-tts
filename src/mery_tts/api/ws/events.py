from collections.abc import AsyncIterator

from mery_tts.audio.encoder import AudioEncoder
from mery_tts.engines.base import PCMChunk


async def synthesize_events(
    session_id: str,
    stream: AsyncIterator[PCMChunk],
    *,
    request_id: str,
) -> AsyncIterator[dict[str, object]]:
    yield {
        "schema_version": "v1",
        "request_id": request_id,
        "event_type": "synthesize.started",
        "session_id": session_id,
    }
    index = 0
    async for chunk in stream:
        yield {
            "schema_version": "v1",
            "request_id": request_id,
            "event_type": "audio.chunk",
            "session_id": session_id,
            "chunk_index": index,
            "audio": AudioEncoder.encode_chunk(chunk),
        }
        index += 1
    yield {
        "schema_version": "v1",
        "request_id": request_id,
        "event_type": "audio.completed",
        "session_id": session_id,
    }

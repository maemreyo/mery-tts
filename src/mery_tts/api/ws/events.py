from collections.abc import AsyncIterator

from mery_tts.audio.encoder import AudioEncoder
from mery_tts.engines.base import PCMChunk


async def synthesize_events(
    session_id: str,
    stream: AsyncIterator[PCMChunk],
) -> AsyncIterator[dict[str, object]]:
    yield {"event_type": "synthesize.started", "session_id": session_id}
    index = 0
    async for chunk in stream:
        yield {
            "event_type": "audio.chunk",
            "session_id": session_id,
            "chunk_index": index,
            "audio": AudioEncoder.encode_chunk(chunk),
        }
        index += 1
    yield {"event_type": "audio.done", "session_id": session_id}

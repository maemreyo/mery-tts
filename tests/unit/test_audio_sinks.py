import base64
from collections.abc import AsyncIterator

import pytest

from mery_tts.audio.encoder import AudioEncoder
from mery_tts.audio.player import AudioPlayer
from mery_tts.engines.base import PCMChunk


async def chunks() -> AsyncIterator[PCMChunk]:
    yield PCMChunk(pcm=b"one", sample_rate_hz=24_000, channels=1)
    yield PCMChunk(pcm=b"two", sample_rate_hz=24_000, channels=1)


@pytest.mark.asyncio
async def test_audio_player_drains_stream_and_stops() -> None:
    writes: list[bytes] = []
    player = AudioPlayer(write=lambda chunk: writes.append(chunk.pcm))

    await player.play(chunks())
    player.stop()

    assert writes == [b"one", b"two"]
    assert player.stopped is True


def test_audio_encoder_round_trips_pcm_bytes() -> None:
    chunk = PCMChunk(pcm=b"fixture", sample_rate_hz=24_000, channels=1)

    encoded = AudioEncoder.encode_chunk(chunk)

    assert base64.b64decode(encoded) == b"fixture"

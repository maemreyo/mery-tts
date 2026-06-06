import base64
import wave
from collections.abc import Sequence
from io import BytesIO

from mery_tts.engines.base import PCMChunk


class AudioEncoder:
    @staticmethod
    def encode_chunk(chunk: PCMChunk) -> str:
        return base64.b64encode(chunk.pcm).decode("ascii")


def encode_wav(chunks: Sequence[PCMChunk]) -> bytes:
    if not chunks:
        raise ValueError("cannot encode empty PCM stream")
    first = chunks[0]
    metadata = (first.sample_rate_hz, first.channels)
    for chunk in chunks:
        if (chunk.sample_rate_hz, chunk.channels) != metadata:
            raise ValueError("unstable PCM metadata")
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(first.channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(first.sample_rate_hz)
        wav_file.writeframes(b"".join(chunk.pcm for chunk in chunks))
    return buffer.getvalue()

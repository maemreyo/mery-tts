import base64

from mery_tts.engines.base import PCMChunk


class AudioEncoder:
    @staticmethod
    def encode_chunk(chunk: PCMChunk) -> str:
        return base64.b64encode(chunk.pcm).decode("ascii")

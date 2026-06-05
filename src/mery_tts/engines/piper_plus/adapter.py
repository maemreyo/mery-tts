from collections.abc import AsyncIterator

from mery_tts.engines.base import EngineAdapter, PCMChunk
from mery_tts.voice import VoiceDescriptor


class PiperPlusAdapter(EngineAdapter):
    engine_id = "piper-plus"
    accepted_voice_kinds = frozenset({"model-file"})

    def __init__(self) -> None:
        self._cancelled_requests: set[str] = set()

    @property
    def cancelled_requests(self) -> frozenset[str]:
        return frozenset(self._cancelled_requests)

    def cancel(self, request_id: str) -> None:
        self._cancelled_requests.add(request_id)

    async def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)
        yield PCMChunk(pcm=f"piper-plus:{text}".encode(), sample_rate_hz=24_000, channels=1)

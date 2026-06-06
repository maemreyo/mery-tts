import asyncio
import importlib.util
from collections.abc import AsyncIterator, Callable, Iterable

from mery_tts.engines.base import EngineAdapter, PCMChunk
from mery_tts.voice import ModelFileVoicePayload, VoiceDescriptor

PiperSynthesizer = Callable[[str, VoiceDescriptor], Iterable[bytes]]


def _default_piper_synthesizer(text: str, voice: VoiceDescriptor) -> Iterable[bytes]:
    if importlib.util.find_spec("piper") is None:
        raise RuntimeError("dependency_missing: piper-plus package is not installed")
    if not isinstance(voice.payload, ModelFileVoicePayload):
        raise RuntimeError("model_missing: piper-plus requires a model-file voice payload")
    raise RuntimeError("model_missing: piper-plus model loading is not configured for this voice")


class PiperPlusAdapter(EngineAdapter):
    engine_id = "piper-plus"
    accepted_voice_kinds = frozenset({"model-file"})

    def __init__(self, synthesizer: PiperSynthesizer | None = None) -> None:
        self._cancelled_requests: set[str] = set()
        self._synthesizer = synthesizer or _default_piper_synthesizer

    @property
    def cancelled_requests(self) -> frozenset[str]:
        return frozenset(self._cancelled_requests)

    def health(self) -> str:
        if (
            importlib.util.find_spec("piper") is None
            and self._synthesizer is _default_piper_synthesizer
        ):
            return "dependency_missing: piper-plus package is not installed"
        return "available"

    def cancel(self, request_id: str) -> None:
        self._cancelled_requests.add(request_id)

    async def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)
        chunks = await asyncio.to_thread(lambda: list(self._synthesizer(text, voice)))
        for index, pcm in enumerate(chunks):
            if voice.voice_id in self._cancelled_requests or "*" in self._cancelled_requests:
                break
            _ = index
            yield PCMChunk(pcm=pcm, sample_rate_hz=24_000, channels=1)

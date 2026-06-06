import asyncio
import importlib.util
from collections.abc import AsyncIterator, Callable, Iterable

from mery_tts.engines.base import EngineAdapter, PCMChunk
from mery_tts.voice import PresetVoicePayload, VoiceDescriptor

KokoroSynthesizer = Callable[[str, VoiceDescriptor], Iterable[bytes]]


def _default_kokoro_synthesizer(text: str, voice: VoiceDescriptor) -> Iterable[bytes]:
    if (
        importlib.util.find_spec("kokoro") is None
        and importlib.util.find_spec("kokoro_onnx") is None
    ):
        raise RuntimeError("dependency_missing: kokoro package is not installed")
    if not isinstance(voice.payload, PresetVoicePayload):
        raise RuntimeError("model_missing: kokoro requires a preset voice payload")
    raise RuntimeError("model_missing: kokoro pipeline loading is not configured for this voice")


class KokoroAdapter(EngineAdapter):
    engine_id = "kokoro"
    accepted_voice_kinds = frozenset({"preset"})

    def __init__(self, synthesizer: KokoroSynthesizer | None = None) -> None:
        self._cancelled_requests: set[str] = set()
        self._synthesizer = synthesizer or _default_kokoro_synthesizer

    @property
    def cancelled_requests(self) -> frozenset[str]:
        return frozenset(self._cancelled_requests)

    def health(self) -> str:
        has_kokoro = importlib.util.find_spec("kokoro") is not None
        has_kokoro_onnx = importlib.util.find_spec("kokoro_onnx") is not None
        if not (has_kokoro or has_kokoro_onnx) and self._synthesizer is _default_kokoro_synthesizer:
            return "dependency_missing: kokoro package is not installed"
        return "available"

    def cancel(self, request_id: str) -> None:
        self._cancelled_requests.add(request_id)

    async def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)
        chunks = await asyncio.to_thread(lambda: list(self._synthesizer(text, voice)))
        for pcm in chunks:
            if voice.voice_id in self._cancelled_requests or "*" in self._cancelled_requests:
                break
            yield PCMChunk(pcm=pcm, sample_rate_hz=24_000, channels=1)

from typing import TYPE_CHECKING

from mery_tts.voice.descriptor import VoiceDescriptor

if TYPE_CHECKING:
    from mery_tts.engines.base import EngineAdapter


class VoiceRegistry:
    def __init__(self, adapters: dict[str, "EngineAdapter"] | None = None) -> None:
        self._adapters = adapters or {}
        self._voices: dict[str, VoiceDescriptor] = {}
        self._routes: dict[str, tuple[EngineAdapter, VoiceDescriptor]] = {}

    def register(self, voice: VoiceDescriptor) -> None:
        self._voices[voice.voice_id] = voice
        adapter = self._adapters.get(voice.engine_id)
        if adapter is not None:
            adapter.ensure_voice_supported(voice)
            self._routes[voice.voice_id] = (adapter, voice)

    def refresh(self, voices: list[VoiceDescriptor]) -> None:
        new_voices: dict[str, VoiceDescriptor] = {}
        new_routes: dict[str, tuple[EngineAdapter, VoiceDescriptor]] = {}
        for voice in voices:
            new_voices[voice.voice_id] = voice
            adapter = self._adapters.get(voice.engine_id)
            if adapter is not None:
                adapter.ensure_voice_supported(voice)
                new_routes[voice.voice_id] = (adapter, voice)
        self._voices = new_voices
        self._routes = new_routes

    def resolve(self, voice_id: str) -> VoiceDescriptor:
        try:
            return self._voices[voice_id]
        except KeyError as exc:
            raise KeyError(f"Unknown voice '{voice_id}'.") from exc

    def resolve_for_adapter(self, voice_id: str, adapter: "EngineAdapter") -> VoiceDescriptor:
        voice = self.resolve(voice_id)
        adapter.ensure_voice_supported(voice)
        return voice

    def resolve_route(self, voice_id: str) -> tuple["EngineAdapter", VoiceDescriptor]:
        try:
            return self._routes[voice_id]
        except KeyError as exc:
            raise KeyError(f"Unknown voice route '{voice_id}'.") from exc

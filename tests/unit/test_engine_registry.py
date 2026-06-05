from collections.abc import AsyncIterator
from dataclasses import dataclass

from mery_tts.engines.base import EngineAdapter, EngineRegistry, PCMChunk
from mery_tts.voice import PresetVoicePayload, VoiceDescriptor, VoiceRegistry


class WorkingAdapter(EngineAdapter):
    engine_id = "working"
    accepted_voice_kinds = frozenset({"preset"})

    async def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)
        yield PCMChunk(pcm=text.encode(), sample_rate_hz=24_000, channels=1)


@dataclass(frozen=True)
class FakeEntryPoint:
    name: str
    adapter_class: type[EngineAdapter] | None

    def load(self) -> type[EngineAdapter]:
        if self.adapter_class is None:
            raise ImportError("optional dependency missing")
        return self.adapter_class


def test_engine_registry_discovers_adapters_and_skips_failed_loads() -> None:
    registry = EngineRegistry.from_entry_points(
        [
            FakeEntryPoint(name="working", adapter_class=WorkingAdapter),
            FakeEntryPoint(name="broken", adapter_class=None),
        ]
    )

    assert registry.engine_ids == ("working",)
    assert registry.load_warnings == ("broken: optional dependency missing",)


def test_engine_registry_allows_zero_adapter_startup() -> None:
    registry = EngineRegistry.from_entry_points([])

    assert registry.engine_ids == ()
    assert registry.adapters == {}


def test_voice_registry_refresh_swaps_routes_without_invalidating_old_adapter() -> None:
    adapter = WorkingAdapter()
    old_voice = VoiceDescriptor(
        voice_id="voice.old",
        engine_id="working",
        payload=PresetVoicePayload(preset_id="old"),
    )
    new_voice = VoiceDescriptor(
        voice_id="voice.new",
        engine_id="working",
        payload=PresetVoicePayload(preset_id="new"),
    )
    registry = VoiceRegistry({"working": adapter})
    registry.refresh([old_voice])
    active_adapter, active_voice = registry.resolve_route("voice.old")

    registry.refresh([new_voice])

    assert active_adapter is adapter
    assert active_voice == old_voice
    assert registry.resolve_route("voice.new") == (adapter, new_voice)

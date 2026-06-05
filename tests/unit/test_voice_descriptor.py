from collections.abc import AsyncIterator

import pytest

from mery_tts.engines.base import EngineAdapter, PCMChunk
from mery_tts.voice import DesignedVoicePayload, PresetVoicePayload, VoiceDescriptor, VoiceRegistry


class FakePresetAdapter(EngineAdapter):
    engine_id = "fake-preset"
    accepted_voice_kinds = frozenset({"preset"})

    async def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)
        yield PCMChunk(pcm=b"pcm", sample_rate_hz=24_000, channels=1)


def test_voice_registry_accepts_adapter_supported_payload_kind() -> None:
    registry = VoiceRegistry()
    voice = VoiceDescriptor(
        voice_id="voice.en.test",
        engine_id="fake-preset",
        payload=PresetVoicePayload(preset_id="en-test"),
    )
    registry.register(voice)

    assert registry.resolve_for_adapter("voice.en.test", FakePresetAdapter()) == voice


def test_voice_registry_rejects_adapter_unsupported_payload_kind() -> None:
    registry = VoiceRegistry()
    registry.register(
        VoiceDescriptor(
            voice_id="voice.designed.test",
            engine_id="fake-preset",
            payload=DesignedVoicePayload(design_id="calm-narrator", parameters={"pace": "slow"}),
        )
    )

    with pytest.raises(ValueError, match="does not accept voice kind 'designed'"):
        registry.resolve_for_adapter("voice.designed.test", FakePresetAdapter())

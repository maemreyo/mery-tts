from collections.abc import AsyncIterator

import pytest

from mery_tts.engines.base import EngineAdapter, PCMChunk
from mery_tts.voice import (
    DesignedVoicePayload,
    ModelFileVoicePayload,
    PresetVoicePayload,
    VoiceDescriptor,
    VoiceRegistry,
)


class FakePresetAdapter(EngineAdapter):
    engine_id = "fake-preset"
    accepted_voice_kinds = frozenset({"preset"})

    async def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[PCMChunk]:
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


@pytest.mark.parametrize(
    "relative_path",
    [
        "/tmp/voice.onnx",
        "../voice.onnx",
        "models/../voice.onnx",
        "models\\voice.onnx",
        "C:\\voice.onnx",
    ],
)
def test_model_file_voice_payload_rejects_unsafe_relative_paths(relative_path: str) -> None:
    with pytest.raises(ValueError, match="safe relative path"):
        ModelFileVoicePayload(artifact_id="artifact", relative_path=relative_path)


@pytest.mark.parametrize(
    "unsafe_voice_id",
    [
        "../secret",
        "a/b",
        "a\\b",
        "/tmp/voice",
        "C:\\voice",
        "http://example.com/voice",
        "https://example.com/voice",
        "file:///tmp/voice",
        "~/voice",
        "~voice",
    ],
)
def test_voice_descriptor_rejects_unsafe_voice_ids(unsafe_voice_id: str) -> None:
    from mery_tts.security.guards import reject_unsafe_identifier

    with pytest.raises(ValueError):
        reject_unsafe_identifier(unsafe_voice_id)

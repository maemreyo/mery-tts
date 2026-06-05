import pytest

from mery_tts.engines.kokoro.adapter import KokoroAdapter
from mery_tts.engines.piper_plus.adapter import PiperPlusAdapter
from mery_tts.voice import ModelFileVoicePayload, PresetVoicePayload, VoiceDescriptor


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("adapter", "voice"),
    [
        (
            PiperPlusAdapter(),
            VoiceDescriptor(
                voice_id="piper.vi.demo",
                engine_id="piper-plus",
                payload=ModelFileVoicePayload(
                    artifact_id="artifact-piper",
                    relative_path="voice.onnx",
                ),
            ),
        ),
        (
            KokoroAdapter(),
            VoiceDescriptor(
                voice_id="kokoro.en.demo",
                engine_id="kokoro",
                payload=PresetVoicePayload(preset_id="af_heart"),
            ),
        ),
    ],
)
async def test_first_party_adapters_expose_contract(adapter, voice) -> None:
    assert adapter.health() == "available"
    assert adapter.accepts_voice(voice)
    chunks = [chunk async for chunk in adapter.synthesize("hello", voice)]

    assert adapter.voices() == ()
    assert chunks[0].pcm
    assert chunks[0].sample_rate_hz == 24_000
    adapter.cancel("req-1")
    assert adapter.cancelled_requests == frozenset({"req-1"})


def test_adapters_reject_wrong_payload_family() -> None:
    adapter = KokoroAdapter()
    voice = VoiceDescriptor(
        voice_id="bad",
        engine_id="kokoro",
        payload=ModelFileVoicePayload(artifact_id="artifact", relative_path="voice.onnx"),
    )

    with pytest.raises(ValueError, match="does not accept voice kind"):
        adapter.ensure_voice_supported(voice)

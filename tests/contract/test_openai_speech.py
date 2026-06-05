from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from mery_tts.api.app import create_app
from mery_tts.engines.base import EngineAdapter, EngineRegistry, PCMChunk
from mery_tts.security.config import HelperConfig
from mery_tts.voice import PresetVoicePayload, VoiceDescriptor, VoiceRegistry

TOKEN = "secret" * 8


class SpeechAdapter(EngineAdapter):
    engine_id = "fake"
    accepted_voice_kinds = frozenset({"preset"})

    async def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)
        yield PCMChunk(pcm=f"pcm:{text}".encode(), sample_rate_hz=24_000, channels=1)


def app_with_voice():
    adapter = SpeechAdapter()
    voice = VoiceDescriptor(
        voice_id="voice.fake",
        engine_id="fake",
        payload=PresetVoicePayload(preset_id="fake"),
    )
    voices = VoiceRegistry({"fake": adapter})
    voices.refresh([voice])
    return create_app(
        config=HelperConfig(helper_id="mery-test", auth_token=TOKEN, port=8765),
        engine_registry=EngineRegistry(adapters={"fake": adapter}),
        voice_registry=voices,
        voice_aliases={"alloy": "voice.fake"},
    )


def test_openai_blocking_speech_returns_pcm_bytes() -> None:
    with TestClient(app_with_voice()) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"model": "tts-1", "voice": "alloy", "input": "hello", "response_format": "pcm"},
        )

    assert response.status_code == 200
    assert response.content == b"pcm:hello"


def test_openai_speech_rejects_unsupported_format() -> None:
    with TestClient(app_with_voice()) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"model": "tts-1", "voice": "alloy", "input": "hello", "response_format": "mp3"},
        )

    assert response.status_code == 400
    assert response.json()["error"]["type"] == "invalid_request_error"


def test_openai_streaming_speech_returns_ordered_pcm_chunks() -> None:
    with TestClient(app_with_voice()) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": "hello",
                "response_format": "pcm",
                "stream": True,
            },
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/pcm"
    assert response.content == b"pcm:hello"

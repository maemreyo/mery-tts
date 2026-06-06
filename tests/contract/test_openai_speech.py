from collections.abc import AsyncIterator

import pytest
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


class UnstableMetadataAdapter(SpeechAdapter):
    async def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)
        yield PCMChunk(pcm=b"first", sample_rate_hz=24_000, channels=1)
        yield PCMChunk(pcm=b"second", sample_rate_hz=48_000, channels=1)


def app_with_voice(
    *,
    adapter: EngineAdapter | None = None,
    max_body_bytes: int = 1_000_000,
    max_text_chars: int = 10_000,
):
    adapter = adapter or SpeechAdapter()
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
        max_body_bytes=max_body_bytes,
        max_text_chars=max_text_chars,
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


def test_openai_blocking_speech_returns_wav_bytes() -> None:
    with TestClient(app_with_voice()) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"model": "tts-1", "voice": "alloy", "input": "hello", "response_format": "wav"},
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content[:4] == b"RIFF"
    assert response.content[8:12] == b"WAVE"
    assert b"pcm:hello" in response.content


def test_openai_speech_requires_authentication() -> None:
    with TestClient(app_with_voice()) as client:
        response = client.post(
            "/v1/audio/speech",
            json={"model": "tts-1", "voice": "alloy", "input": "hello"},
        )

    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "auth.token_missing"
    assert body["request_id"] == "local"
    assert body["category"] == "auth"
    assert "recommended_action" in body


def test_openai_speech_rejects_unsupported_method_and_unknown_route() -> None:
    with TestClient(app_with_voice()) as client:
        unsupported_method = client.get(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        unknown_route = client.post(
            "/v1/audio/unknown",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"model": "tts-1", "voice": "alloy", "input": "hello"},
        )

    assert unsupported_method.status_code == 405
    assert unknown_route.status_code == 404


def test_openai_errors_remain_separate_from_native_error_shape() -> None:
    with TestClient(app_with_voice()) as client:
        openai_response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"model": "gpt-4o-mini-tts", "voice": "alloy", "input": "hello"},
        )
        native_response = client.post(
            "/v1/models/install",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"schema_version": "v1", "request_id": "local", "model_id": "../secret"},
        )

    assert openai_response.status_code == 400
    assert openai_response.json() == {
        "error": {
            "message": "unsupported model",
            "type": "invalid_request_error",
        }
    }
    assert native_response.status_code == 400
    assert native_response.json()["code"] == "security.unsafe_identifier"


def test_openai_speech_rejects_unsupported_model() -> None:
    with TestClient(app_with_voice()) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"model": "gpt-4o-mini-tts", "voice": "alloy", "input": "hello"},
        )

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "message": "unsupported model",
            "type": "invalid_request_error",
        }
    }


def test_openai_speech_rejects_unsupported_format() -> None:
    with TestClient(app_with_voice()) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"model": "tts-1", "voice": "alloy", "input": "hello", "response_format": "mp3"},
        )

    assert response.status_code == 400
    assert response.json()["error"]["type"] == "invalid_request_error"


def test_openai_speech_rejects_too_long_input() -> None:
    with TestClient(app_with_voice(max_body_bytes=1_000_000, max_text_chars=128)) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"model": "tts-1", "voice": "alloy", "input": "x" * 129},
        )

    assert response.status_code == 413
    body = response.json()
    assert body["code"] == "security.request_too_large"
    assert body["category"] == "security"
    assert body["recommended_action"] == "none"
    assert body["fallback_policy"] == "none"
    assert body["request_id"] == "local"


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


def test_openai_streaming_speech_rejects_non_pcm_format_before_streaming() -> None:
    with TestClient(app_with_voice()) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": "hello",
                "response_format": "wav",
                "stream": True,
            },
        )

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "message": "streaming only supports pcm",
            "type": "invalid_request_error",
        }
    }


def test_openai_streaming_speech_propagates_mid_stream_adapter_errors() -> None:
    with (
        TestClient(app_with_voice(adapter=UnstableMetadataAdapter())) as client,
        pytest.raises(ValueError, match="unstable PCM metadata"),
    ):
        client.post(
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


def test_openai_streaming_speech_uses_http_transport_without_ws_events() -> None:
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
    assert b"event_type" not in response.content
    assert response.content == b"pcm:hello"

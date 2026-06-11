import asyncio
import threading
from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from mery_tts.api.app import create_app
from mery_tts.api.openai.speech import OpenAISpeechRequest
from mery_tts.engines.base import EngineAdapter, EngineRegistry, PCMChunk
from mery_tts.models.store import ModelStore
from mery_tts.security.config import HelperConfig
from mery_tts.storage.identity import StorageIdentityStore
from mery_tts.voice import PresetVoicePayload, VoiceDescriptor, VoiceRegistry

TOKEN = "secret" * 8


class SpeechAdapter(EngineAdapter):
    engine_id = "fake"
    accepted_voice_kinds = frozenset({"preset"})

    async def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)
        yield PCMChunk(pcm=f"pcm:{text}".encode(), sample_rate_hz=24_000, channels=1)


class CountingAdapter(SpeechAdapter):
    def __init__(self) -> None:
        self.calls = 0
        self.texts: list[str] = []

    async def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[PCMChunk]:
        self.calls += 1
        self.texts.append(text)
        async for chunk in super().synthesize(text, voice, request_id=request_id):
            yield chunk


class ReferenceCapableAdapter(SpeechAdapter):
    accepted_voice_kinds = frozenset({"preset", "reference"})

    def __init__(self) -> None:
        self.called = False

    async def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[PCMChunk]:
        self.called = True
        self.ensure_voice_supported(voice)
        yield PCMChunk(pcm=f"pcm:{text}".encode(), sample_rate_hz=24_000, channels=1)


class SlowAdapter(SpeechAdapter):
    def __init__(self) -> None:
        self.cancelled = False

    async def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[PCMChunk]:
        try:
            await asyncio.sleep(1.0)
            yield PCMChunk(pcm=f"pcm:{text}".encode(), sample_rate_hz=24_000, channels=1)
        except asyncio.CancelledError:
            self.cancelled = True
            raise


class BlockingAdapter(SpeechAdapter):
    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()
        self.calls = 0

    async def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[PCMChunk]:
        self.calls += 1
        self.started.set()
        await asyncio.to_thread(self.release.wait)
        yield PCMChunk(pcm=f"pcm:{text}".encode(), sample_rate_hz=24_000, channels=1)


class UnstableMetadataAdapter(SpeechAdapter):
    async def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)
        yield PCMChunk(pcm=b"first", sample_rate_hz=24_000, channels=1)
        yield PCMChunk(pcm=b"second", sample_rate_hz=48_000, channels=1)


def app_with_voice(
    *,
    adapter: EngineAdapter | None = None,
    voice: VoiceDescriptor | None = None,
    max_body_bytes: int = 1_000_000,
    max_text_chars: int = 10_000,
    provider_network_policy: dict[str, str] | None = None,
    local_only: bool = False,
    air_gapped: bool = False,
    provider_concurrency_limits: dict[str, int] | None = None,
    provider_queue_limits: dict[str, int] | None = None,
    default_timeout_seconds: float | None = None,
    provider_timeout_overrides: dict[str, float] | None = None,
):
    adapter = adapter or SpeechAdapter()
    voice = voice or VoiceDescriptor(
        voice_id="voice.fake",
        engine_id="fake",
        payload=PresetVoicePayload(preset_id="fake"),
        supported_locales=["en-US"],
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
        provider_network_policy=provider_network_policy,
        local_only=local_only,
        air_gapped=air_gapped,
        provider_concurrency_limits=provider_concurrency_limits,
        provider_queue_limits=provider_queue_limits,
        default_timeout_seconds=default_timeout_seconds,
        provider_timeout_overrides=provider_timeout_overrides,
    )


async def _call_speech(client: TestClient, text: str):
    return await asyncio.to_thread(
        client.post,
        "/v1/audio/speech",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"model": "tts-1", "voice": "alloy", "input": text, "response_format": "pcm"},
    )


@pytest.mark.asyncio
async def test_openai_blocking_speech_returns_busy_when_provider_queue_overflows() -> None:
    adapter = BlockingAdapter()
    app = app_with_voice(
        adapter=adapter,
        provider_concurrency_limits={"fake": 1},
        provider_queue_limits={"fake": 0},
    )

    with TestClient(app) as client:
        first = asyncio.create_task(_call_speech(client, "first"))
        await asyncio.to_thread(adapter.started.wait)
        second = await _call_speech(client, "second")
        adapter.release.set()
        first_response = await first

    assert first_response.status_code == 200
    assert second.status_code == 429
    body = second.json()
    assert body["code"] == "connection.rate_limited"
    assert body["category"] == "connection"
    assert "reason=provider_busy" in body["sanitized_diagnostic"]
    assert "provider_id=fake" in body["sanitized_diagnostic"]
    assert adapter.calls == 1


@pytest.mark.asyncio
async def test_provider_concurrency_slot_releases_after_cancelled_request() -> None:
    adapter = BlockingAdapter()
    app = app_with_voice(
        adapter=adapter,
        provider_concurrency_limits={"fake": 1},
        provider_queue_limits={"fake": 0},
    )

    with TestClient(app) as client:
        first = asyncio.create_task(_call_speech(client, "first"))
        await asyncio.to_thread(adapter.started.wait)
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        adapter.release.set()
        second = await _call_speech(client, "second")

    assert second.status_code == 200
    assert second.content == b"pcm:second"


def test_openai_blocking_speech_uses_request_lower_timeout_and_cleans_up() -> None:
    adapter = SlowAdapter()
    app = app_with_voice(adapter=adapter, default_timeout_seconds=5.0)

    with TestClient(app) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": "hello",
                "response_format": "pcm",
                "mery": {"timeoutSeconds": 0.01},
            },
        )

    assert response.status_code == 504
    body = response.json()
    assert body["code"] == "connection.timeout"
    assert body["category"] == "connection"
    assert "reason=synthesis_timeout" in body["sanitized_diagnostic"]
    assert "provider_id=fake" in body["sanitized_diagnostic"]
    assert "timeout_seconds=0.01" in body["sanitized_diagnostic"]
    assert adapter.cancelled is True


def test_request_timeout_cannot_extend_provider_override() -> None:
    adapter = SlowAdapter()
    app = app_with_voice(
        adapter=adapter,
        default_timeout_seconds=5.0,
        provider_timeout_overrides={"fake": 0.01},
    )

    with TestClient(app) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": "hello",
                "response_format": "pcm",
                "mery": {"timeoutSeconds": 30.0},
            },
        )

    assert response.status_code == 504
    assert "timeout_seconds=0.01" in response.json()["sanitized_diagnostic"]


def test_openai_speech_request_accepts_optional_normalized_locale() -> None:
    request = OpenAISpeechRequest(
        model="tts-1",
        voice="alloy",
        input="xin chao",
        locale="VI-vn",
    )
    legacy_request = OpenAISpeechRequest(model="tts-1", voice="alloy", input="hello")

    assert request.locale == "vi-VN"
    assert legacy_request.locale is None


@pytest.mark.parametrize("invalid_locale", ["", "vietnamese", "vi_vn", "vi-"])
def test_openai_speech_request_rejects_invalid_locale(invalid_locale: str) -> None:
    with pytest.raises(ValueError, match="valid BCP-47"):
        OpenAISpeechRequest(
            model="tts-1",
            voice="alloy",
            input="hello",
            locale=invalid_locale,
        )


def test_openai_blocking_speech_applies_core_locale_text_normalization_before_adapter() -> None:
    with TestClient(app_with_voice()) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": "“Hello”…",
                "response_format": "pcm",
                "locale": "en-US",
            },
        )

    assert response.status_code == 200
    assert response.content == b'pcm:"Hello"...'


def test_openai_blocking_speech_segments_text_with_sanitized_diagnostics() -> None:
    adapter = CountingAdapter()
    raw_text = "One. Two? Three!"
    with TestClient(app_with_voice(adapter=adapter)) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": raw_text,
                "response_format": "pcm",
                "locale": "en-US",
            },
        )

    assert response.status_code == 200
    assert adapter.texts == ["One.", "Two?", "Three!"]
    assert response.content == b"pcm:One.pcm:Two?pcm:Three!"
    assert response.headers["X-Mery-Normalizer-Version"] == "core-text-v1"
    assert response.headers["X-Mery-Normalization-Locale"] == "en-US"
    assert response.headers["X-Mery-Normalization-Categories"] == (
        "unicode_nfkc,punctuation_ascii,whitespace_collapse,segmentation"
    )
    assert response.headers["X-Mery-Normalization-Warnings"] == ""
    assert response.headers["X-Mery-Normalization-Length-Before"] == str(len(raw_text))
    assert response.headers["X-Mery-Normalization-Length-After"] == str(len(raw_text))
    assert response.headers["X-Mery-Segment-Count"] == "3"
    assert raw_text not in str(response.headers)


def test_openai_blocking_speech_accepts_optional_locale_without_breaking_synthesis() -> None:
    with TestClient(app_with_voice()) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": "xin chao",
                "response_format": "pcm",
                "locale": "en-US",
            },
        )

    assert response.status_code == 200
    assert response.content == b"pcm:xin chao"


def test_openai_blocking_speech_blocks_remote_provider_when_local_only() -> None:
    adapter = ReferenceCapableAdapter()
    app = app_with_voice(
        adapter=adapter,
        provider_network_policy={"fake": "remote"},
        local_only=True,
        air_gapped=True,
    )

    with TestClient(app) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": "hello",
                "response_format": "pcm",
            },
        )

    assert response.status_code == 503
    body = response.json()
    assert body["code"] == "connection.timeout"
    assert body["category"] == "connection"
    diagnostic = body["sanitized_diagnostic"]
    assert "reason=network_disabled" in diagnostic
    assert "policy=air_gapped" in diagnostic
    assert "operation=remote_provider" in diagnostic
    assert "provider_id=fake" in diagnostic
    assert adapter.called is False


def test_openai_blocking_speech_rejects_gated_reference_voice() -> None:
    adapter = ReferenceCapableAdapter()
    voice = VoiceDescriptor(
        voice_id="voice.fake",
        engine_id="fake",
        payload=PresetVoicePayload(preset_id="fake"),
        supported_locales=["en-US"],
        risk_class="reference",
        consent_required=True,
        consent_status="pending",
    )

    with TestClient(app_with_voice(adapter=adapter, voice=voice)) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": "hello",
                "response_format": "pcm",
            },
        )

    assert response.status_code == 403
    body = response.json()
    assert body["code"] == "synthesis.gated_feature"
    assert body["category"] == "synthesis"
    assert body["fallback_policy"] == "disable_feature"
    assert body["sanitized_diagnostic"] == (
        "reason=gated_feature,risk_class=reference,voice_id=voice.fake"
    )
    assert adapter.called is False
    assert "hello" not in str(body)


def test_openai_blocking_speech_rejects_locale_mismatch_with_sanitized_diagnostics() -> None:
    with TestClient(app_with_voice()) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": "xin chao",
                "response_format": "pcm",
                "locale": "vi-VN",
            },
        )

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "synthesis.locale_mismatch"
    assert body["category"] == "synthesis"
    assert body["sanitized_diagnostic"] == (
        "reason=locale_mismatch,requested_locale=vi-VN,"
        "selected_voice_locale=en-US,voice_id=voice.fake"
    )
    assert "xin chao" not in str(body)


def test_openai_blocking_speech_returns_pcm_bytes() -> None:
    with TestClient(app_with_voice()) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"model": "tts-1", "voice": "alloy", "input": "hello", "response_format": "pcm"},
        )

    assert response.status_code == 200
    assert response.content == b"pcm:hello"


def test_app_startup_hydrates_installed_voice_manifest_into_routing_map(tmp_path) -> None:
    adapter = SpeechAdapter()
    store = StorageIdentityStore(tmp_path)
    store.write_artifact_manifest(
        engine_id="fake",
        artifact_id="artifact.fake",
        metadata={"catalogEntryId": "voice.fake"},
    )
    store.write_voice_manifest(
        "voice.fake",
        ["artifact.fake"],
        {"kind": "preset", "preset_id": "fake"},
    )
    app = create_app(
        config=HelperConfig(helper_id="mery-test", auth_token=TOKEN, port=8765),
        engine_registry=EngineRegistry(adapters={"fake": adapter}),
        voice_registry=VoiceRegistry({"fake": adapter}),
        voice_aliases={"alloy": "voice.fake"},
        model_store=ModelStore(tmp_path),
        storage_identity_store=store,
    )

    with TestClient(app) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"model": "tts-1", "voice": "alloy", "input": "hello", "response_format": "pcm"},
        )

    assert response.status_code == 200
    assert response.content == b"pcm:hello"


def test_delete_commit_refresh_removes_voice_route_from_registry(tmp_path) -> None:
    adapter = SpeechAdapter()
    store = StorageIdentityStore(tmp_path)
    store.write_artifact_manifest(
        engine_id="fake",
        artifact_id="artifact.fake",
        metadata={"catalogEntryId": "voice.fake"},
    )
    store.write_voice_manifest(
        "voice.fake",
        ["artifact.fake"],
        {"kind": "preset", "preset_id": "fake"},
    )
    app = create_app(
        config=HelperConfig(helper_id="mery-test", auth_token=TOKEN, port=8765),
        engine_registry=EngineRegistry(adapters={"fake": adapter}),
        voice_registry=VoiceRegistry({"fake": adapter}),
        voice_aliases={"alloy": "voice.fake"},
        model_store=ModelStore(tmp_path),
        storage_identity_store=store,
    )

    with TestClient(app) as client:
        deleted = client.delete(
            "/v1/models/voice.fake",
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"model": "tts-1", "voice": "alloy", "input": "hello", "response_format": "pcm"},
        )

    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert response.status_code == 400
    body = response.json()
    assert "code" in body or "error" in body


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


@pytest.mark.parametrize("response_format", ["mp3", "ogg", "aac", "opus"])
def test_openai_speech_rejects_unsupported_compressed_formats_without_fallback(
    response_format: str,
) -> None:
    adapter = CountingAdapter()
    with TestClient(app_with_voice(adapter=adapter)) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": "hello",
                "response_format": response_format,
            },
        )

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "synthesis.unsupported_format"
    assert body["category"] == "synthesis"
    assert body["fallback_policy"] == "none"
    assert "unsupported response_format" in body["sanitized_diagnostic"]
    assert adapter.calls == 0


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
    assert response.headers["content-type"] == "audio/L16;rate=24000;channels=1"
    assert response.headers["x-mery-audio-encoding"] == "pcm_s16le"
    assert response.headers["x-mery-sample-rate"] == "24000"
    assert response.headers["x-mery-channels"] == "1"
    assert response.headers["x-mery-sample-width-bytes"] == "2"
    assert response.headers["x-mery-stream-format"] == "raw-pcm"
    assert response.headers["x-accel-buffering"] == "no"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-mery-request-id"].startswith("req-")
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


def test_openai_streaming_speech_marks_mid_stream_adapter_errors_as_lifecycle_failure() -> None:
    with TestClient(app_with_voice(adapter=UnstableMetadataAdapter())) as client:
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
    assert response.content == b"first"


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
    assert response.headers["content-type"] == "audio/L16;rate=24000;channels=1"
    assert b"event_type" not in response.content
    assert response.content == b"pcm:hello"

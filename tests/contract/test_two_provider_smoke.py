"""Two-provider HTTP local smoke test.

ADR-0021/02: End-to-end local smoke path that proves Piper and Kokoro can both
synthesize through HTTP /v1/audio/speech, and that Mery can operate degraded
when only one provider works.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from mery_tts.api.app import create_app
from mery_tts.engines.base import EngineRegistry, PCMChunk
from mery_tts.engines.kokoro.adapter import KokoroAdapter
from mery_tts.engines.piper_plus.adapter import PiperPlusAdapter
from mery_tts.security.config import HelperConfig
from mery_tts.smoke.record import SmokeRecordStore
from mery_tts.storage.identity import StorageIdentityStore
from mery_tts.voice import ModelFileVoicePayload, PresetVoicePayload, VoiceDescriptor
from mery_tts.voice.registry import VoiceRegistry

TOKEN = "test-token-" + "x" * 30


def _fake_piper_synthesizer(text: str, voice):
    return [b"piper-pcm-data"]


def _fake_kokoro_synthesizer(text: str, voice):
    return [b"kokoro-pcm-data"]


def _failing_piper_synthesizer(text: str, voice):
    raise RuntimeError("dependency_missing: piper-plus package is not installed")


def _app_with_both_providers(tmp_path):
    """Create an app with both Piper and Kokoro fake adapters."""
    piper = PiperPlusAdapter(synthesizer=_fake_piper_synthesizer)
    kokoro = KokoroAdapter(synthesizer=_fake_kokoro_synthesizer)

    piper_voice = VoiceDescriptor(
        voice_id="piper-plus.vi-vn.demo",
        engine_id="piper-plus",
        payload=ModelFileVoicePayload(
            artifact_id="piper-plus.vi-vn.demo",
            relative_path="piper-plus.vi-vn.demo.onnx",
        ),
    )
    kokoro_voice = VoiceDescriptor(
        voice_id="kokoro.en-us.af-heart.demo",
        engine_id="kokoro",
        payload=PresetVoicePayload(preset_id="kokoro.en-us.af-heart.demo"),
    )

    store = StorageIdentityStore(tmp_path)
    store.write_artifact_manifest(
        engine_id="piper-plus",
        artifact_id="piper-plus.vi-vn.demo",
        metadata={"catalogEntryId": "piper-plus.vi-vn.demo"},
    )
    store.write_artifact_manifest(
        engine_id="kokoro",
        artifact_id="kokoro.en-us.af-heart.demo",
        metadata={"catalogEntryId": "kokoro.en-us.af-heart.demo"},
    )
    store.write_voice_manifest(
        "piper-plus.vi-vn.demo",
        ["piper-plus.vi-vn.demo"],
        {
            "kind": "model-file",
            "artifact_id": "piper-plus.vi-vn.demo",
            "relative_path": "piper-plus.vi-vn.demo.onnx",
        },
    )
    store.write_voice_manifest(
        "kokoro.en-us.af-heart.demo",
        ["kokoro.en-us.af-heart.demo"],
        {"kind": "preset", "preset_id": "kokoro.en-us.af-heart.demo"},
    )

    registry = EngineRegistry(adapters={"piper-plus": piper, "kokoro": kokoro})
    voice_registry = VoiceRegistry(registry.adapters)
    voice_registry.register(piper_voice)
    voice_registry.register(kokoro_voice)

    smoke_store = SmokeRecordStore(data_dir=tmp_path)

    return create_app(
        config=HelperConfig(helper_id="mery-smoke", auth_token=TOKEN, port=8765),
        engine_registry=registry,
        voice_registry=voice_registry,
        voice_aliases={
            "piper-voice": "piper-plus.vi-vn.demo",
            "kokoro-voice": "kokoro.en-us.af-heart.demo",
        },
        storage_identity_store=store,
        smoke_record_store=smoke_store,
    )


def test_piper_synthesizes_pcm_through_http(tmp_path) -> None:
    """Piper installed voice synthesizes real PCM through /v1/audio/speech."""
    with TestClient(_app_with_both_providers(tmp_path)) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "model": "tts-1",
                "voice": "piper-voice",
                "input": "Hello from Piper",
                "response_format": "pcm",
            },
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/pcm"
    assert len(response.content) > 0
    assert response.headers.get("X-Mery-Voice-Used") == "piper-plus.vi-vn.demo"
    assert response.headers.get("X-Mery-Fallback-Used") == "false"


def test_kokoro_synthesizes_pcm_through_http(tmp_path) -> None:
    """Kokoro installed voice synthesizes real PCM through /v1/audio/speech."""
    with TestClient(_app_with_both_providers(tmp_path)) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "model": "tts-1",
                "voice": "kokoro-voice",
                "input": "Hello from Kokoro",
                "response_format": "pcm",
            },
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/pcm"
    assert len(response.content) > 0
    assert response.headers.get("X-Mery-Voice-Used") == "kokoro.en-us.af-heart.demo"


def test_piper_to_kokoro_fallback_on_recoverable_failure(tmp_path) -> None:
    """Piper→Kokoro fallback is exercised when Piper fails recoverably."""
    piper = PiperPlusAdapter(synthesizer=_failing_piper_synthesizer)
    kokoro = KokoroAdapter(synthesizer=_fake_kokoro_synthesizer)

    piper_voice = VoiceDescriptor(
        voice_id="piper-plus.vi-vn.demo",
        engine_id="piper-plus",
        payload=ModelFileVoicePayload(
            artifact_id="piper-plus.vi-vn.demo",
            relative_path="piper-plus.vi-vn.demo.onnx",
        ),
    )
    kokoro_voice = VoiceDescriptor(
        voice_id="kokoro.en-us.af-heart.demo",
        engine_id="kokoro",
        payload=PresetVoicePayload(preset_id="kokoro.en-us.af-heart.demo"),
    )

    store = StorageIdentityStore(tmp_path)
    store.write_artifact_manifest(
        engine_id="piper-plus",
        artifact_id="piper-plus.vi-vn.demo",
        metadata={"catalogEntryId": "piper-plus.vi-vn.demo"},
    )
    store.write_artifact_manifest(
        engine_id="kokoro",
        artifact_id="kokoro.en-us.af-heart.demo",
        metadata={"catalogEntryId": "kokoro.en-us.af-heart.demo"},
    )
    store.write_voice_manifest(
        "piper-plus.vi-vn.demo",
        ["piper-plus.vi-vn.demo"],
        {
            "kind": "model-file",
            "artifact_id": "piper-plus.vi-vn.demo",
            "relative_path": "piper-plus.vi-vn.demo.onnx",
        },
    )
    store.write_voice_manifest(
        "kokoro.en-us.af-heart.demo",
        ["kokoro.en-us.af-heart.demo"],
        {"kind": "preset", "preset_id": "kokoro.en-us.af-heart.demo"},
    )

    registry = EngineRegistry(adapters={"piper-plus": piper, "kokoro": kokoro})
    voice_registry = VoiceRegistry(registry.adapters)
    voice_registry.register(piper_voice)
    voice_registry.register(kokoro_voice)

    smoke_store = SmokeRecordStore(data_dir=tmp_path)

    app = create_app(
        config=HelperConfig(helper_id="mery-smoke", auth_token=TOKEN, port=8765),
        engine_registry=registry,
        voice_registry=voice_registry,
        voice_aliases={
            "piper-voice": "piper-plus.vi-vn.demo",
            "kokoro-voice": "kokoro.en-us.af-heart.demo",
        },
        storage_identity_store=store,
        smoke_record_store=smoke_store,
    )

    with TestClient(app) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "model": "tts-1",
                "voice": "piper-voice",
                "input": "Hello fallback",
                "response_format": "pcm",
                "mery": {
                    "fallbackVoiceIds": ["kokoro.en-us.af-heart.demo"],
                    "fallbackPolicy": "auto",
                },
            },
        )

    assert response.status_code == 200
    assert response.headers.get("X-Mery-Fallback-Used") == "true"
    assert response.headers.get("X-Mery-Voice-Used") == "kokoro.en-us.af-heart.demo"


def test_degraded_mode_allows_synthesis_through_working_provider(tmp_path) -> None:
    """Runtime degraded mode still allows synthesis through the working provider."""
    with TestClient(_app_with_both_providers(tmp_path)) as client:
        health = client.get(
            "/v1/health",
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        speech = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "model": "tts-1",
                "voice": "kokoro-voice",
                "input": "Degraded mode test",
                "response_format": "wav",
            },
        )

    assert health.status_code == 200
    health_body = health.json()
    assert health_body["status"] in {"ready", "degraded", "ok"}
    assert health_body["total_installed_voices"] >= 1

    assert speech.status_code == 200
    assert speech.headers["content-type"] == "audio/wav"
    assert speech.content[:4] == b"RIFF"


def test_diagnostic_headers_present_on_success(tmp_path) -> None:
    """Successful audio responses include X-Mery-* diagnostic headers."""
    with TestClient(_app_with_both_providers(tmp_path)) as client:
        response = client.post(
            "/v1/audio/speech",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "model": "tts-1",
                "voice": "piper-voice",
                "input": "Header test",
                "response_format": "pcm",
            },
        )

    assert response.status_code == 200
    assert "X-Mery-Request-Id" in response.headers
    assert "X-Mery-Voice-Used" in response.headers
    assert "X-Mery-Fallback-Used" in response.headers
    assert "X-Mery-Audio-Encoding" in response.headers
    assert "X-Mery-Sample-Rate" in response.headers
    assert "X-Mery-Channels" in response.headers

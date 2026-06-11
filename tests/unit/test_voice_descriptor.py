from collections.abc import AsyncIterator

import pytest
from pydantic import ValidationError

from mery_tts.engines.base import EngineAdapter, PCMChunk
from mery_tts.governance import VoiceGovernanceMetadata
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


def test_voice_descriptor_normalizes_supported_locales_additively() -> None:
    voice = VoiceDescriptor(
        voice_id="voice.vi.test",
        engine_id="fake-preset",
        payload=PresetVoicePayload(preset_id="vi-test"),
        supported_locales=["VI-vn", "en-us", "vi-VN"],
    )

    assert voice.supported_locales == ["vi-VN", "en-US"]
    assert VoiceDescriptor(
        voice_id="voice.legacy.test",
        engine_id="fake-preset",
        payload=PresetVoicePayload(preset_id="legacy"),
    ).supported_locales == []


@pytest.mark.parametrize("invalid_locale", ["", "english", "en_Us", "en-", "1n-US"])
def test_voice_descriptor_rejects_invalid_supported_locales(invalid_locale: str) -> None:
    with pytest.raises(ValidationError, match="valid BCP-47"):
        VoiceDescriptor(
            voice_id="voice.invalid.test",
            engine_id="fake-preset",
            payload=PresetVoicePayload(preset_id="invalid"),
            supported_locales=[invalid_locale],
        )


@pytest.mark.parametrize(
    "risk_class",
    ["stock", "designed", "reference", "cloned", "dialogue", "conversion"],
)
def test_voice_descriptor_accepts_voice_risk_classes(risk_class: str) -> None:
    voice = VoiceDescriptor(
        voice_id=f"voice.{risk_class}.test",
        engine_id="fake-preset",
        payload=PresetVoicePayload(preset_id=risk_class),
        risk_class=risk_class,
        license_id="license.fixture",
        license_scope="offline-local-use",
        provenance="bundled fixture catalog",
        consent_required=risk_class != "stock",
        consent_status="pending" if risk_class != "stock" else "not_required",
    )

    assert voice.risk_class == risk_class
    assert voice.license_id == "license.fixture"
    assert voice.license_scope == "offline-local-use"
    assert voice.provenance == "bundled fixture catalog"


def test_voice_descriptor_defaults_missing_governance_to_stock() -> None:
    voice = VoiceDescriptor(
        voice_id="voice.legacy.test",
        engine_id="fake-preset",
        payload=PresetVoicePayload(preset_id="legacy"),
    )

    assert voice.risk_class == "stock"
    assert voice.license_id is None
    assert voice.license_scope is None
    assert voice.provenance is None
    assert voice.consent_required is False
    assert voice.consent_status == "not_required"
    assert VoiceGovernanceMetadata().risk_class == "stock"


def test_voice_descriptor_rejects_unknown_risk_class() -> None:
    with pytest.raises(ValidationError):
        VoiceDescriptor(
            voice_id="voice.unknown.test",
            engine_id="fake-preset",
            payload=PresetVoicePayload(preset_id="unknown"),
            risk_class="celebrity",
        )


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

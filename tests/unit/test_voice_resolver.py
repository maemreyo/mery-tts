"""Unit tests for InstalledVoiceResolver — focuses on native_sample_rate_hz propagation.

ADR-0024 follow-up: the resolver reads the native sample rate from the
Piper config JSON once during resolution and caches it on the payload.
Downstream consumers (engine adapters, capability endpoints) use the
cached value and never need to re-read the config.

These tests exercise the resolver in isolation against a tmp_path
artifact directory, without loading the piper package or real models.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mery_tts.voice import ModelFileVoicePayload, VoiceDescriptor
from mery_tts.voice.resolver import (
    InstalledVoiceResolver,
    VoiceResolutionError,
)


def _build_artifact(tmp_path: Path, engine_id: str, artifact_id: str, config: dict) -> Path:
    artifact_dir = tmp_path / "artifacts" / engine_id / artifact_id
    artifact_dir.mkdir(parents=True)
    model = artifact_dir / "voice.onnx"
    model.write_bytes(b"\x00" * 16)
    config_file = artifact_dir / "voice.onnx.json"
    config_file.write_text(json.dumps(config))
    return artifact_dir


def test_resolver_populates_nested_audio_sample_rate(tmp_path: Path) -> None:
    artifact_dir = _build_artifact(
        tmp_path, "piper-plus", "amy-low", {"audio": {"sample_rate": 16_000}}
    )

    resolver = InstalledVoiceResolver(artifacts_dir=tmp_path / "artifacts")
    voice = VoiceDescriptor(
        voice_id="piper.en-us.amy.low",
        engine_id="piper-plus",
        payload=ModelFileVoicePayload(
            artifact_id="amy-low",
            relative_path="voice.onnx",
        ),
    )
    resolved = resolver.resolve(voice)

    assert resolved.payload.config_path == artifact_dir / "voice.onnx.json"
    assert resolved.payload.native_sample_rate_hz == 16_000


def test_resolver_populates_top_level_sample_rate_fallback(tmp_path: Path) -> None:
    _build_artifact(tmp_path, "piper-plus", "legacy", {"sample_rate": 22_050})

    resolver = InstalledVoiceResolver(artifacts_dir=tmp_path / "artifacts")
    voice = VoiceDescriptor(
        voice_id="piper.legacy.voice",
        engine_id="piper-plus",
        payload=ModelFileVoicePayload(
            artifact_id="legacy",
            relative_path="voice.onnx",
        ),
    )
    resolved = resolver.resolve(voice)

    assert resolved.payload.native_sample_rate_hz == 22_050


def test_resolver_nested_takes_precedence_over_top_level(tmp_path: Path) -> None:
    _build_artifact(
        tmp_path,
        "piper-plus",
        "mixed",
        {"audio": {"sample_rate": 16_000}, "sample_rate": 22_050},
    )

    resolver = InstalledVoiceResolver(artifacts_dir=tmp_path / "artifacts")
    voice = VoiceDescriptor(
        voice_id="piper.mixed.voice",
        engine_id="piper-plus",
        payload=ModelFileVoicePayload(
            artifact_id="mixed",
            relative_path="voice.onnx",
        ),
    )
    resolved = resolver.resolve(voice)

    assert resolved.payload.native_sample_rate_hz == 16_000


def test_resolver_returns_none_when_config_lacks_sample_rate(tmp_path: Path) -> None:
    _build_artifact(tmp_path, "piper-plus", "no-rate", {"voice": "demo"})

    resolver = InstalledVoiceResolver(artifacts_dir=tmp_path / "artifacts")
    voice = VoiceDescriptor(
        voice_id="piper.no-rate.voice",
        engine_id="piper-plus",
        payload=ModelFileVoicePayload(
            artifact_id="no-rate",
            relative_path="voice.onnx",
        ),
    )
    resolved = resolver.resolve(voice)

    assert resolved.payload.native_sample_rate_hz is None
    assert resolved.payload.config_path is not None


def test_resolver_returns_none_when_config_is_malformed(tmp_path: Path) -> None:
    artifact_dir = _build_artifact(
        tmp_path, "piper-plus", "broken", {"audio": {"sample_rate": 16_000}}
    )
    (artifact_dir / "voice.onnx.json").write_text("{not valid json")

    resolver = InstalledVoiceResolver(artifacts_dir=tmp_path / "artifacts")
    voice = VoiceDescriptor(
        voice_id="piper.broken.voice",
        engine_id="piper-plus",
        payload=ModelFileVoicePayload(
            artifact_id="broken",
            relative_path="voice.onnx",
        ),
    )
    resolved = resolver.resolve(voice)

    assert resolved.payload.native_sample_rate_hz is None


def test_resolver_preserves_payload_fields(tmp_path: Path) -> None:
    _build_artifact(tmp_path, "piper-plus", "amy-low", {"audio": {"sample_rate": 16_000}})

    resolver = InstalledVoiceResolver(artifacts_dir=tmp_path / "artifacts")
    voice = VoiceDescriptor(
        voice_id="piper.en-us.amy.low",
        engine_id="piper-plus",
        payload=ModelFileVoicePayload(
            artifact_id="amy-low",
            relative_path="voice.onnx",
        ),
    )
    resolved = resolver.resolve(voice)

    assert resolved.voice_id == "piper.en-us.amy.low"
    assert resolved.engine_id == "piper-plus"
    assert resolved.payload.artifact_id == "amy-low"
    assert (
        resolved.payload.model_path
        == tmp_path / "artifacts" / "piper-plus" / "amy-low" / "voice.onnx"
    )


def test_resolver_raises_for_missing_artifact(tmp_path: Path) -> None:
    resolver = InstalledVoiceResolver(artifacts_dir=tmp_path / "artifacts")
    voice = VoiceDescriptor(
        voice_id="piper.missing.voice",
        engine_id="piper-plus",
        payload=ModelFileVoicePayload(
            artifact_id="does-not-exist",
            relative_path="voice.onnx",
        ),
    )

    with pytest.raises(VoiceResolutionError, match="missing artifact"):
        resolver.resolve(voice)

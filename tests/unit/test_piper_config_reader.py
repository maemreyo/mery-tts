"""Unit tests for PiperConfigReader — standalone config JSON reader.

These tests exercise the reader in isolation, without importing the
piper package or any mery_tts module beyond stdlib. The reader must
never raise on missing/malformed files — it returns ``None`` so the
caller can fall back to defaults gracefully.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mery_tts.engines.piper_plus.config import PiperConfigReader


@pytest.fixture
def reader() -> PiperConfigReader:
    return PiperConfigReader()


def test_nested_audio_sample_rate_is_returned(reader: PiperConfigReader, tmp_path: Path) -> None:
    config = tmp_path / "voice.onnx.json"
    config.write_text(
        json.dumps(
            {"audio": {"sample_rate": 16_000, "quality": "low"}, "espeak": {"voice": "en-us"}}
        )
    )
    assert reader.read_sample_rate_hz(config) == 16_000


def test_top_level_sample_rate_is_fallback(reader: PiperConfigReader, tmp_path: Path) -> None:
    config = tmp_path / "voice.onnx.json"
    config.write_text(json.dumps({"sample_rate": 22_050}))
    assert reader.read_sample_rate_hz(config) == 22_050


def test_nested_audio_takes_precedence_over_top_level(
    reader: PiperConfigReader, tmp_path: Path
) -> None:
    config = tmp_path / "voice.onnx.json"
    config.write_text(json.dumps({"audio": {"sample_rate": 16_000}, "sample_rate": 22_050}))
    assert reader.read_sample_rate_hz(config) == 16_000


def test_missing_file_returns_none(reader: PiperConfigReader, tmp_path: Path) -> None:
    assert reader.read_sample_rate_hz(tmp_path / "does_not_exist.json") is None


def test_malformed_json_returns_none(reader: PiperConfigReader, tmp_path: Path) -> None:
    config = tmp_path / "voice.onnx.json"
    config.write_text("{not valid json")
    assert reader.read_sample_rate_hz(config) is None


def test_non_dict_json_returns_none(reader: PiperConfigReader, tmp_path: Path) -> None:
    config = tmp_path / "voice.onnx.json"
    config.write_text(json.dumps([1, 2, 3]))
    assert reader.read_sample_rate_hz(config) is None


def test_missing_field_returns_none(reader: PiperConfigReader, tmp_path: Path) -> None:
    config = tmp_path / "voice.onnx.json"
    config.write_text(json.dumps({"audio": {"quality": "low"}, "espeak": {}}))
    assert reader.read_sample_rate_hz(config) is None


def test_non_int_value_returns_none(reader: PiperConfigReader, tmp_path: Path) -> None:
    config = tmp_path / "voice.onnx.json"
    config.write_text(json.dumps({"audio": {"sample_rate": "16000"}}))
    assert reader.read_sample_rate_hz(config) is None


def test_zero_value_returns_none(reader: PiperConfigReader, tmp_path: Path) -> None:
    config = tmp_path / "voice.onnx.json"
    config.write_text(json.dumps({"audio": {"sample_rate": 0}}))
    assert reader.read_sample_rate_hz(config) is None


def test_negative_value_returns_none(reader: PiperConfigReader, tmp_path: Path) -> None:
    config = tmp_path / "voice.onnx.json"
    config.write_text(json.dumps({"audio": {"sample_rate": -1}}))
    assert reader.read_sample_rate_hz(config) is None


def test_audio_present_but_not_dict_returns_none(reader: PiperConfigReader, tmp_path: Path) -> None:
    config = tmp_path / "voice.onnx.json"
    config.write_text(json.dumps({"audio": "not a dict"}))
    assert reader.read_sample_rate_hz(config) is None


def test_empty_dict_returns_none(reader: PiperConfigReader, tmp_path: Path) -> None:
    config = tmp_path / "voice.onnx.json"
    config.write_text(json.dumps({}))
    assert reader.read_sample_rate_hz(config) is None


def test_reader_is_stateless_and_reusable(reader: PiperConfigReader, tmp_path: Path) -> None:
    config_a = tmp_path / "a.json"
    config_a.write_text(json.dumps({"audio": {"sample_rate": 16_000}}))
    config_b = tmp_path / "b.json"
    config_b.write_text(json.dumps({"sample_rate": 22_050}))

    assert reader.read_sample_rate_hz(config_a) == 16_000
    assert reader.read_sample_rate_hz(config_b) == 22_050
    assert reader.read_sample_rate_hz(config_a) == 16_000


def test_real_piper_amy_low_schema(reader: PiperConfigReader, tmp_path: Path) -> None:
    """Mirror the real en_US-amy-low.onnx.json shipped by Piper."""
    config = tmp_path / "en_US-amy-low.onnx.json"
    config.write_text(
        json.dumps(
            {
                "audio": {"sample_rate": 16_000, "quality": "low", "channels": 1},
                "espeak": {"voice": "en-us"},
                "inference": {"noise_scale": 0.667, "length_scale": 1.0, "noise_w": 0.8},
                "phoneme_type": "espeak",
                "phoneme_map": {},
                "speaker_id_map": {},
            }
        )
    )
    assert reader.read_sample_rate_hz(config) == 16_000

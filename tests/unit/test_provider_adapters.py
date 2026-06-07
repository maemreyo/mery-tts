import importlib.util
import json

import pytest

from mery_tts.engines.base import EngineAdapter
from mery_tts.engines.kokoro.adapter import KokoroAdapter
from mery_tts.engines.piper_plus.adapter import PiperPlusAdapter
from mery_tts.providers.taxonomy import assert_provider_payload_allowed
from mery_tts.streaming.capabilities import StreamingCapability
from mery_tts.voice import ModelFileVoicePayload, PresetVoicePayload, VoiceDescriptor
from mery_tts.voice.resolver import ResolvedModelFilePayload, ResolvedVoice


def piper_voice() -> VoiceDescriptor:
    return VoiceDescriptor(
        voice_id="piper.vi.demo",
        engine_id="piper-plus",
        payload=ModelFileVoicePayload(
            artifact_id="artifact-piper",
            relative_path="voice.onnx",
        ),
    )


def kokoro_voice() -> VoiceDescriptor:
    return VoiceDescriptor(
        voice_id="kokoro.en.demo",
        engine_id="kokoro",
        payload=PresetVoicePayload(preset_id="af_heart"),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("adapter", "voice", "prefix"),
    [
        (
            PiperPlusAdapter(synthesizer=lambda text, voice: [f"piper-plus:{text}".encode()]),
            piper_voice(),
            b"piper-plus:hello",
        ),
        (
            KokoroAdapter(synthesizer=lambda text, voice: [f"kokoro:{text}".encode()]),
            kokoro_voice(),
            b"kokoro:hello",
        ),
    ],
)
async def test_first_party_adapters_expose_contract(adapter, voice, prefix: bytes) -> None:
    assert_provider_payload_allowed(voice.payload.kind)
    assert adapter.health() == "available"
    assert adapter.accepts_voice(voice)
    chunks = [chunk async for chunk in adapter.synthesize("hello", voice)]

    assert adapter.voices() == ()
    assert chunks[0].pcm == prefix
    assert chunks[0].sample_rate_hz == 24_000
    adapter.cancel("req-1")
    assert adapter.cancelled_requests == frozenset({"req-1"})


@pytest.mark.asyncio
async def test_adapters_stop_streaming_after_voice_cancellation() -> None:
    adapter = KokoroAdapter(synthesizer=lambda text, voice: [b"first", b"second"])
    voice = kokoro_voice()
    adapter.cancel(voice.voice_id)

    chunks = [chunk async for chunk in adapter.synthesize("hello", voice)]

    assert chunks == []


def test_adapters_reject_wrong_payload_family() -> None:
    adapter = KokoroAdapter()
    voice = VoiceDescriptor(
        voice_id="bad",
        engine_id="kokoro",
        payload=ModelFileVoicePayload(artifact_id="artifact", relative_path="voice.onnx"),
    )

    with pytest.raises(ValueError, match="does not accept voice kind"):
        adapter.ensure_voice_supported(voice)


def test_default_adapters_report_missing_optional_dependencies_without_import_failure() -> None:
    piper_health = PiperPlusAdapter().health()
    kokoro_health = KokoroAdapter().health()

    assert piper_health in {"available", "dependency_missing: piper-plus package is not installed"}
    assert kokoro_health in {"available", "dependency_missing: kokoro package is not installed"}


@pytest.mark.engine
@pytest.mark.asyncio
async def test_piper_plus_real_runtime_smoke_skips_without_dependency() -> None:
    if importlib.util.find_spec("piper") is None:
        pytest.skip(
            "piper-plus real-runtime smoke requires optional piper package and fixture model"
        )
    pytest.skip("manual piper-plus smoke requires configured fixture model path")


@pytest.mark.engine
@pytest.mark.asyncio
async def test_kokoro_real_runtime_smoke_skips_without_dependency() -> None:
    has_kokoro = importlib.util.find_spec("kokoro") is not None
    has_kokoro_onnx = importlib.util.find_spec("kokoro_onnx") is not None
    if not (has_kokoro or has_kokoro_onnx):
        pytest.skip("kokoro real-runtime smoke requires optional kokoro package and fixture voice")
    pytest.skip("manual kokoro smoke requires configured fixture voice/model")


def test_piper_plus_streaming_capability_reports_not_supported_without_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _find_spec(name: str) -> None:
        return None

    monkeypatch.setattr(importlib.util, "find_spec", _find_spec)
    adapter = PiperPlusAdapter()

    info = adapter.streaming_capability()

    assert info.supported is False
    assert info.mode is StreamingCapability.NOT_SUPPORTED


def test_piper_plus_streaming_capability_reports_sentence_chunked_with_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name: object() if name == "piper" else None
    )
    adapter = PiperPlusAdapter()

    info = adapter.streaming_capability()

    assert info.supported is True
    assert info.mode is StreamingCapability.SENTENCE_CHUNKED
    assert info.granularity == "sentence"
    assert info.true_incremental is False
    assert info.format == "pcm_s16le"
    assert 24_000 in info.sample_rates_hz


def test_kokoro_streaming_capability_reports_not_supported_without_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: None)
    adapter = KokoroAdapter()

    info = adapter.streaming_capability()

    assert info.supported is False
    assert info.mode is StreamingCapability.NOT_SUPPORTED


def test_kokoro_streaming_capability_reports_sentence_chunked_with_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name: object() if name == "kokoro_onnx" else None
    )
    adapter = KokoroAdapter()

    info = adapter.streaming_capability()

    assert info.supported is True
    assert info.mode is StreamingCapability.SENTENCE_CHUNKED
    assert info.granularity == "sentence"
    assert info.true_incremental is False
    assert info.format == "pcm_s16le"
    assert 24_000 in info.sample_rates_hz


def test_piper_plus_voice_streaming_capability_returns_baseline_without_resolved_voice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name: object() if name == "piper" else None
    )
    adapter = PiperPlusAdapter()

    info = adapter.voice_streaming_capability(piper_voice())

    assert info.sample_rates_hz == (22_050, 24_000)


def test_piper_plus_voice_streaming_capability_narrows_to_native_rate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name: object() if name == "piper" else None
    )
    config_path = tmp_path / "voice.onnx.json"
    config_path.write_text(json.dumps({"sample_rate": 22_050}))
    adapter = PiperPlusAdapter()
    voice = piper_voice()
    adapter.register_resolved_voice(
        ResolvedVoice(
            voice_id=voice.voice_id,
            engine_id=voice.engine_id,
            payload=ResolvedModelFilePayload(
                artifact_id="artifact-piper",
                model_path=tmp_path / "voice.onnx",
                config_path=config_path,
            ),
        )
    )

    info = adapter.voice_streaming_capability(voice)

    assert info.sample_rates_hz == (22_050,)


def test_piper_plus_voice_streaming_capability_returns_baseline_when_config_lacks_sample_rate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name: object() if name == "piper" else None
    )
    config_path = tmp_path / "voice.onnx.json"
    config_path.write_text(json.dumps({"voice": "demo"}))
    adapter = PiperPlusAdapter()
    voice = piper_voice()
    adapter.register_resolved_voice(
        ResolvedVoice(
            voice_id=voice.voice_id,
            engine_id=voice.engine_id,
            payload=ResolvedModelFilePayload(
                artifact_id="artifact-piper",
                model_path=tmp_path / "voice.onnx",
                config_path=config_path,
            ),
        )
    )

    info = adapter.voice_streaming_capability(voice)

    assert info.sample_rates_hz == (22_050, 24_000)


def test_piper_plus_voice_streaming_capability_returns_baseline_when_config_unreadable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name: object() if name == "piper" else None
    )
    config_path = tmp_path / "voice.onnx.json"
    config_path.write_text("not valid json")
    adapter = PiperPlusAdapter()
    voice = piper_voice()
    adapter.register_resolved_voice(
        ResolvedVoice(
            voice_id=voice.voice_id,
            engine_id=voice.engine_id,
            payload=ResolvedModelFilePayload(
                artifact_id="artifact-piper",
                model_path=tmp_path / "voice.onnx",
                config_path=config_path,
            ),
        )
    )

    info = adapter.voice_streaming_capability(voice)

    assert info.sample_rates_hz == (22_050, 24_000)


def test_kokoro_voice_streaming_capability_returns_baseline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name: object() if name == "kokoro_onnx" else None
    )
    adapter = KokoroAdapter()

    info = adapter.voice_streaming_capability(kokoro_voice())

    assert info.sample_rates_hz == (24_000,)


def test_streaming_capability_mode_enum_values_are_snake_case() -> None:
    assert StreamingCapability.NOT_SUPPORTED.value == "not_supported"
    assert StreamingCapability.ROUTE_CHUNKED.value == "route_chunked"
    assert StreamingCapability.SENTENCE_CHUNKED.value == "sentence_chunked"
    assert StreamingCapability.NATIVE_INCREMENTAL.value == "native_incremental"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("adapter", "voice"),
    [
        (
            PiperPlusAdapter(synthesizer=lambda text, voice: [b"piper-pcm-1", b"piper-pcm-2"]),
            piper_voice(),
        ),
        (
            KokoroAdapter(synthesizer=lambda text, voice: [b"kokoro-pcm-1", b"kokoro-pcm-2"]),
            kokoro_voice(),
        ),
    ],
)
async def test_first_party_adapters_emit_richer_pcm_chunks(
    adapter: EngineAdapter,
    voice: VoiceDescriptor,
) -> None:
    chunks = [chunk async for chunk in adapter.synthesize("hello", voice)]

    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk.sample_width_bytes == 2
        assert chunk.encoding == "pcm_s16le"
        assert chunk.sample_rate_hz == 24_000
        assert chunk.channels == 1


@pytest.mark.asyncio
async def test_piper_plus_synthesize_uses_native_rate_from_resolved_payload(
    tmp_path,
) -> None:
    class _FakeVoice:
        def synthesize_stream_raw(self, text: str):
            return [b"\x00\x00", b"\x00\x00", b"\x00\x00"]

    class _FakeCache:
        def get_or_load(self, voice_id: str, resolved: ResolvedVoice):
            return _FakeVoice()

    adapter = PiperPlusAdapter(runtime_cache=_FakeCache())
    voice = piper_voice()
    adapter.register_resolved_voice(
        ResolvedVoice(
            voice_id=voice.voice_id,
            engine_id=voice.engine_id,
            payload=ResolvedModelFilePayload(
                artifact_id="artifact-piper",
                model_path=tmp_path / "voice.onnx",
                config_path=tmp_path / "voice.onnx.json",
                native_sample_rate_hz=16_000,
            ),
        )
    )

    chunks = [chunk async for chunk in adapter.synthesize("hello", voice)]

    assert len(chunks) == 3
    for chunk in chunks:
        assert chunk.sample_rate_hz == 16_000
        assert chunk.encoding == "pcm_s16le"
        assert chunk.channels == 1


@pytest.mark.asyncio
async def test_piper_plus_synthesize_falls_back_to_baseline_without_native_rate(
    tmp_path,
) -> None:
    class _FakeVoice:
        def synthesize_stream_raw(self, text: str):
            return [b"\x00\x00"]

    class _FakeCache:
        def get_or_load(self, voice_id: str, resolved: ResolvedVoice):
            return _FakeVoice()

    adapter = PiperPlusAdapter(runtime_cache=_FakeCache())
    voice = piper_voice()
    adapter.register_resolved_voice(
        ResolvedVoice(
            voice_id=voice.voice_id,
            engine_id=voice.engine_id,
            payload=ResolvedModelFilePayload(
                artifact_id="artifact-piper",
                model_path=tmp_path / "voice.onnx",
                config_path=None,
                native_sample_rate_hz=None,
            ),
        )
    )

    chunks = [chunk async for chunk in adapter.synthesize("hello", voice)]

    assert len(chunks) == 1
    assert chunks[0].sample_rate_hz == 24_000


@pytest.mark.asyncio
async def test_piper_plus_voice_streaming_capability_uses_nested_schema(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name: object() if name == "piper" else None
    )
    config_path = tmp_path / "voice.onnx.json"
    config_path.write_text(json.dumps({"audio": {"sample_rate": 16_000}}))
    adapter = PiperPlusAdapter()
    voice = piper_voice()
    adapter.register_resolved_voice(
        ResolvedVoice(
            voice_id=voice.voice_id,
            engine_id=voice.engine_id,
            payload=ResolvedModelFilePayload(
                artifact_id="artifact-piper",
                model_path=tmp_path / "voice.onnx",
                config_path=config_path,
            ),
        )
    )

    info = adapter.voice_streaming_capability(voice)

    assert info.sample_rates_hz == (16_000,)


def test_piper_plus_voice_streaming_capability_uses_pre_resolved_native_rate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name: object() if name == "piper" else None
    )
    adapter = PiperPlusAdapter()
    voice = piper_voice()
    adapter.register_resolved_voice(
        ResolvedVoice(
            voice_id=voice.voice_id,
            engine_id=voice.engine_id,
            payload=ResolvedModelFilePayload(
                artifact_id="artifact-piper",
                model_path=tmp_path / "voice.onnx",
                config_path=None,
                native_sample_rate_hz=16_000,
            ),
        )
    )

    info = adapter.voice_streaming_capability(voice)

    assert info.sample_rates_hz == (16_000,)

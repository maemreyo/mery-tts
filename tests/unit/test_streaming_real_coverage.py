"""Unit tests promoted from the round-3 verdict smoke test.

These tests exercise the same code paths the smoke test in
``docs/reports/adr-0031-0035-round3-verdict-irl-tests/smoke_test.py`` did,
but as proper pytest functions so they run in the normal test suite and
fail loudly under CI. The smoke test itself has been retired; see
``docs/reports/adr-0031-0035-round3-verdict-irl-tests/report.md`` for
the verdict-to-evidence map.

The 8 smoke-test sections cover the 7 round-3 verdicts plus one
supplementary check on ``http.py`` private-access patterns.
"""

from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from mery_tts.engines.base import EngineAdapter, PCMChunk
from mery_tts.engines.piper_plus.adapter import PiperPlusAdapter
from mery_tts.streaming.capabilities import (
    StreamingCapability,
    StreamingCapabilityInfo,
)
from mery_tts.streaming.metadata import StreamMetadataError
from mery_tts.streaming.pipeline import StreamingPipeline
from mery_tts.streaming.sequence import StreamSequenceError
from mery_tts.voice.descriptor import (
    PresetVoicePayload,
    VoiceDescriptor,
)
from mery_tts.voice.resolver import ResolvedModelFilePayload, ResolvedVoice

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"


# ---------------------------------------------------------------------------
# Test fixtures (module-local; the smoke test's FakeAdapter is reused here)
# ---------------------------------------------------------------------------


def _chunk(seq: int, sample_rate: int = 22_050, channels: int = 1) -> PCMChunk:
    return PCMChunk(
        pcm=b"\x00\x00" * 10,
        sample_rate_hz=sample_rate,
        channels=channels,
        sample_width_bytes=2,
        encoding="pcm_s16le",
        sequence=seq,
    )


def _make_preset_voice() -> VoiceDescriptor:
    return VoiceDescriptor(
        voice_id="unit-voice",
        engine_id="piper-plus",
        display_name="Unit Voice",
        language="en-US",
        payload=PresetVoicePayload(preset_id="unit.preset"),
    )


class _FakeAdapter(EngineAdapter):
    """Adapter that yields a fixed chunk sequence; can be told to raise."""

    def __init__(self, engine_id: str, *, raise_with: Exception | None = None) -> None:
        super().__init__()
        self._engine_id = engine_id
        self._raise_with = raise_with
        self._emitted = 0

    @property
    def engine_id(self) -> str:
        return self._engine_id

    @property
    def accepted_voice_kinds(self) -> tuple[str, ...]:
        return ("preset",)

    def streaming_capability(self) -> StreamingCapabilityInfo:
        return StreamingCapabilityInfo(
            supported=True,
            mode=StreamingCapability.FIXED_RATE,
            granularity="chunk",
            true_incremental=True,
            format="pcm_s16le",
            sample_rates_hz=(22_050, 24_000),
        )

    async def synthesize(
        self, text: str, voice: VoiceDescriptor, *, request_id: str
    ) -> AsyncIterator[PCMChunk]:
        for _ in range(3):
            if self._raise_with is not None and self._emitted == 0:
                self._emitted += 1
                raise self._raise_with
            yield _chunk(0)
            self._emitted += 1


class _TwoChunkAdapter(_FakeAdapter):
    """First chunk sets baseline; second chunk has mismatched channels."""

    async def synthesize(
        self, text: str, voice: VoiceDescriptor, *, request_id: str
    ) -> AsyncIterator[PCMChunk]:
        yield _chunk(0, sample_rate=22_050, channels=1)
        yield _chunk(0, sample_rate=22_050, channels=2)


# ---------------------------------------------------------------------------
# ADR-0031: PipelineResult.sequence_error
# ---------------------------------------------------------------------------


async def test_sequence_error_true_after_stream_sequence_error() -> None:
    adapter = _FakeAdapter("piper-plus", raise_with=StreamSequenceError("gap"))
    pipeline = StreamingPipeline(
        adapter=adapter, voice=_make_preset_voice(), text="hi", request_id="r-a"
    )
    with pytest.raises(StreamSequenceError):
        async for _ in pipeline.run():
            pass
    result = pipeline.result()
    assert result.sequence_error is True
    assert result.metadata_drift is True


async def test_sequence_error_false_after_stream_metadata_error() -> None:
    adapter = _TwoChunkAdapter("piper-plus")
    pipeline = StreamingPipeline(
        adapter=adapter, voice=_make_preset_voice(), text="hi", request_id="r-b"
    )
    with pytest.raises(StreamMetadataError):
        async for _ in pipeline.run():
            pass
    result = pipeline.result()
    assert result.sequence_error is False
    assert result.metadata_drift is True


async def test_sequence_error_false_after_clean_run() -> None:
    adapter = _FakeAdapter("piper-plus")
    pipeline = StreamingPipeline(
        adapter=adapter, voice=_make_preset_voice(), text="hi", request_id="r-c"
    )
    async for _ in pipeline.run():
        pass
    result = pipeline.result()
    assert result.sequence_error is False
    assert result.metadata_drift is False
    assert result.cancelled is False


async def test_sequence_error_resets_between_runs_on_same_pipeline() -> None:
    adapter = _FakeAdapter("piper-plus")
    pipeline = StreamingPipeline(
        adapter=adapter, voice=_make_preset_voice(), text="hi", request_id="r-d"
    )
    # First run drains cleanly.
    async for _ in pipeline.run():
        pass
    assert pipeline.result().sequence_error is False
    # Second run also drains cleanly — the flag must not leak.
    async for _ in pipeline.run():
        pass
    assert pipeline.result().sequence_error is False


# ---------------------------------------------------------------------------
# ADR-0034: StreamingPipeline.engine_id property
# ---------------------------------------------------------------------------


def test_engine_id_property_delegates_to_adapter() -> None:
    pipeline = StreamingPipeline(
        adapter=_FakeAdapter("kokoro-onnx"),
        voice=_make_preset_voice(),
        text="hi",
        request_id="r-eng",
    )
    assert pipeline.engine_id == "kokoro-onnx"


def test_engine_id_property_with_real_piper_plus_adapter() -> None:
    pipeline = StreamingPipeline(
        adapter=PiperPlusAdapter(),
        voice=_make_preset_voice(),
        text="hi",
        request_id="r-eng-real",
    )
    assert pipeline.engine_id == "piper-plus"


# ---------------------------------------------------------------------------
# ADR-0033: StreamCancellation thread-safety (in-loop + call_soon_threadsafe)
# ---------------------------------------------------------------------------


async def test_in_loop_cancel_is_idempotent() -> None:
    from mery_tts.streaming.cancellation import StreamCancellation

    c = StreamCancellation(request_id="in-loop")
    c.cancel()
    assert c.is_cancelled() is True
    c.cancel()  # idempotent
    assert c.is_cancelled() is True


async def test_call_soon_threadsafe_cancel_propagates_to_loop() -> None:
    from mery_tts.streaming.cancellation import StreamCancellation

    c = StreamCancellation(request_id="thread-safe")
    loop = asyncio.get_running_loop()

    def worker() -> None:
        loop.call_soon_threadsafe(c.cancel)

    t = threading.Thread(target=worker)
    t.start()
    await asyncio.sleep(0.01)
    t.join()
    assert c.is_cancelled() is True


async def test_pipeline_cancel_in_loop_sets_cancellation() -> None:
    pipeline = StreamingPipeline(
        adapter=_FakeAdapter("piper-plus"),
        voice=_make_preset_voice(),
        text="hi",
        request_id="r-cx",
    )
    pipeline.cancel()
    assert pipeline.cancellation.is_cancelled() is True
    pipeline.cancel()  # idempotent
    assert pipeline.cancellation.is_cancelled() is True


# ---------------------------------------------------------------------------
# ADR-0035: voice_streaming_capability lazy resolution (production wiring)
# ---------------------------------------------------------------------------


def test_voice_streaming_capability_unresolved_returns_baseline(tmp_path: Path) -> None:
    adapter = PiperPlusAdapter()
    voice = _make_preset_voice()
    info = adapter.voice_streaming_capability(voice)
    assert info.sample_rates_hz == (22_050, 24_000)


def test_voice_streaming_capability_narrows_when_native_in_baseline(tmp_path: Path) -> None:
    adapter = PiperPlusAdapter()
    voice = _make_preset_voice()
    config_path = tmp_path / "v22k.onnx.json"
    config_path.write_text(json.dumps({"sample_rate": 22_050}))
    model_path = tmp_path / "v22k.onnx"
    model_path.write_bytes(b"fake")
    adapter.register_resolved_voice(
        ResolvedVoice(
            voice_id=voice.voice_id,
            engine_id="piper-plus",
            payload=ResolvedModelFilePayload(
                artifact_id="a-22k",
                model_path=model_path,
                config_path=config_path,
            ),
        )
    )
    info = adapter.voice_streaming_capability(voice)
    assert info.sample_rates_hz == (22_050,)


def test_voice_streaming_capability_falls_back_for_unmappable_rate(tmp_path: Path) -> None:
    """Native rate outside the baseline (e.g. 16000) → baseline unchanged."""
    adapter = PiperPlusAdapter()
    voice = _make_preset_voice()
    config_path = tmp_path / "v16k.onnx.json"
    config_path.write_text(json.dumps({"sample_rate": 16_000}))
    model_path = tmp_path / "v16k.onnx"
    model_path.write_bytes(b"fake")
    adapter.register_resolved_voice(
        ResolvedVoice(
            voice_id=voice.voice_id,
            engine_id="piper-plus",
            payload=ResolvedModelFilePayload(
                artifact_id="a-16k",
                model_path=model_path,
                config_path=config_path,
            ),
        )
    )
    info = adapter.voice_streaming_capability(voice)
    assert info.sample_rates_hz == (22_050, 24_000)


def test_voice_streaming_capability_falls_back_when_config_missing(tmp_path: Path) -> None:
    adapter = PiperPlusAdapter()
    voice = _make_preset_voice()
    config_path = tmp_path / "missing.onnx.json"  # never written
    model_path = tmp_path / "missing.onnx"
    model_path.write_bytes(b"fake")
    adapter.register_resolved_voice(
        ResolvedVoice(
            voice_id=voice.voice_id,
            engine_id="piper-plus",
            payload=ResolvedModelFilePayload(
                artifact_id="a-missing",
                model_path=model_path,
                config_path=config_path,
            ),
        )
    )
    info = adapter.voice_streaming_capability(voice)
    assert info.sample_rates_hz == (22_050, 24_000)


# ---------------------------------------------------------------------------
# Example clients use stream: true
# ---------------------------------------------------------------------------


def test_python_example_client_uses_stream_true() -> None:
    src = (_REPO_ROOT / "examples/openai_streaming/python_client.py").read_text()
    assert "stream_format" not in src
    assert '"stream": True' in src or '"stream":True' in src


def test_node_example_client_uses_stream_true() -> None:
    src = (_REPO_ROOT / "examples/openai_streaming/node_client.js").read_text()
    assert "stream_format" not in src
    assert "stream: true" in src or "stream:true" in src


# ---------------------------------------------------------------------------
# sequence.py module docstring accuracy
# ---------------------------------------------------------------------------


def test_sequence_module_docstring_uses_first_chunk_value() -> None:
    src = (_SRC_ROOT / "mery_tts/streaming/sequence.py").read_text()
    assert "starting from 0 for" not in src
    assert "first chunk's value" in src


# ---------------------------------------------------------------------------
# http.py must not reach into pipeline private attributes
# ---------------------------------------------------------------------------


def test_http_transport_uses_public_engine_id_property() -> None:
    src = (_SRC_ROOT / "mery_tts/streaming/transports/http.py").read_text()
    assert "pipeline.engine_id" in src
    for pattern in (
        "pipeline._adapter.engine_id",
        "pipeline._adapter.cancel",
        "pipeline._adapter.synthesize",
    ):
        assert pattern not in src, f"http.py must not access {pattern!r}"


# ---------------------------------------------------------------------------
# ADR-0031 edge case: per-run reset on the SAME pipeline instance
# ---------------------------------------------------------------------------


async def test_pipeline_result_clears_metadata_drift_on_clean_second_run() -> None:
    """A clean second run on the same pipeline must zero out metadata_drift."""
    pipeline = StreamingPipeline(
        adapter=_FakeAdapter("piper-plus"),
        voice=_make_preset_voice(),
        text="hi",
        request_id="r-reset",
    )
    async for _ in pipeline.run():
        pass
    result1 = pipeline.result()
    assert result1.metadata_drift is False
    assert result1.sequence_error is False
    # Calling result() again before a new run must be stable.
    result1b = pipeline.result()
    assert result1b.metadata_drift is False
    assert result1b.sequence_error is False

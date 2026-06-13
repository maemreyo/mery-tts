"""Piper Plus engine adapter with runtime caching.

ADR-0024: Piper adapter lazy-loads runtime objects and caches them per installed
voice/artifact. It accepts resolved model-file voices and emits normalized PCMChunk values.

ADR-0024 follow-up: the native sample rate is read from the Piper config JSON
once during voice resolution and carried on the ``ResolvedModelFilePayload``,
so synthesis and capability reporting never need to re-read or re-parse the
config. The engine baseline (24_000 Hz) is used only as a last-resort fallback
when the config is absent or unparseable.
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
from collections.abc import AsyncIterator, Callable, Iterable
from dataclasses import replace
from typing import Protocol, cast

from mery_tts.engines.annotated import AnnotatedSynthesisCapable, AnnotatedSynthesisResult
from mery_tts.engines.base import EngineAdapter, PCMChunk
from mery_tts.engines.piper_plus.config import PiperConfigReader
from mery_tts.engines.piper_plus.timed_session import PiperTimedSession
from mery_tts.streaming.capabilities import StreamingCapability, StreamingCapabilityInfo
from mery_tts.voice import ModelFileVoicePayload, VoiceDescriptor
from mery_tts.voice.resolver import ResolvedModelFilePayload, ResolvedVoice

PiperSynthesizer = Callable[[str, VoiceDescriptor], Iterable[bytes]]

_DEFAULT_SYNTHESIS_SAMPLE_RATE_HZ = 24_000


class _PiperSynthesizedChunk(Protocol):
    audio_int16_bytes: bytes


class _PiperVoice(Protocol):
    """Structural type mirroring ``piper.PiperVoice``."""

    def synthesize(
        self, text: str, *, syn_config: object = ...
    ) -> Iterable[_PiperSynthesizedChunk]: ...


class _PiperRawStreamVoice(Protocol):
    """Compatibility shape exposed by older Piper runtimes and test fakes."""

    def synthesize_stream_raw(self, text: str) -> Iterable[bytes]: ...


class _PiperVoiceFactory(Protocol):
    def load(self, model_path: str, config_path: str | None = None) -> _PiperVoice: ...


class _PiperModule(Protocol):
    PiperVoice: _PiperVoiceFactory


class PiperRuntimeError(Exception):
    """Structured Piper runtime error."""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message


def _default_piper_synthesizer(text: str, voice: VoiceDescriptor) -> Iterable[bytes]:
    if importlib.util.find_spec("piper") is None:
        raise PiperRuntimeError("dependency_missing", "piper-plus package is not installed")
    if not isinstance(voice.payload, ModelFileVoicePayload):
        raise PiperRuntimeError("model_missing", "piper-plus requires a model-file voice payload")
    raise PiperRuntimeError(
        "model_missing", "piper-plus model loading is not configured for this voice"
    )


def _patch_espeak_phoneme_type() -> None:
    """Register 'espeak' as a MULTILINGUAL alias in piper-plus PhonemeType.

    piper-plus ≥ 1.12 removed PhonemeType.ESPEAK.  Voice models trained with
    the original rhasspy piper use ``"phoneme_type": "espeak"`` in their config
    JSON.  The underlying phoneme_id_map in those models is IPA — identical to
    what piper-plus 1.12's MULTILINGUAL phonemizer produces — so loading the
    ONNX with MULTILINGUAL semantics is safe and produces correct output.

    This patch is idempotent: calling it multiple times is harmless.
    """
    try:
        from piper.config import PhonemeType  # noqa: PLC0415 (local import)
        if "espeak" not in PhonemeType._value2member_map_:
            PhonemeType._value2member_map_["espeak"] = PhonemeType.MULTILINGUAL
    except Exception:  # noqa: BLE001 (best-effort patch, never crash)
        pass


class PiperRuntimeCache:
    """Lazy-loading runtime cache for Piper voice instances.

    The cache stores a ``piper.PiperVoice`` per voice_id. The voice
    is loaded via ``piper.PiperVoice.load(model_path, config_path)``
    which is the only supported constructor in the installed
    piper-plus package — there is no ``PiperConfig.load`` or
    ``PiperSynthesizer`` class attribute to call separately.
    """

    def __init__(self) -> None:
        self._cache: dict[str, _PiperVoice] = {}

    def get_or_load(self, voice_id: str, resolved: ResolvedVoice) -> _PiperVoice:
        if voice_id in self._cache:
            return self._cache[voice_id]
        runtime = self._load_runtime(resolved)
        self._cache[voice_id] = runtime
        return runtime

    def invalidate(self, voice_id: str) -> None:
        self._cache.pop(voice_id, None)

    def clear(self) -> None:
        self._cache.clear()

    def _load_runtime(self, resolved: ResolvedVoice) -> _PiperVoice:
        if not isinstance(resolved.payload, ResolvedModelFilePayload):
            raise PiperRuntimeError(
                "model_missing", "piper-plus requires a resolved model-file payload"
            )
        if importlib.util.find_spec("piper") is None:
            raise PiperRuntimeError("dependency_missing", "piper-plus package is not installed")
        try:
            # piper-plus ≥ 1.12 dropped PhonemeType.espeak (models trained with the
            # original rhasspy piper use espeak IPA phoneme IDs which are identical
            # to the multilingual IPA IDs used by piper-plus 1.12).  Register
            # "espeak" as an alias for MULTILINGUAL so legacy voice configs load.
            _patch_espeak_phoneme_type()

            piper = cast(_PiperModule, cast(object, importlib.import_module("piper")))
            model_path = str(resolved.payload.model_path)
            config_path = (
                str(resolved.payload.config_path) if resolved.payload.config_path else None
            )
            if config_path is not None:
                return piper.PiperVoice.load(model_path, config_path)
            return piper.PiperVoice.load(model_path)
        except ImportError as exc:
            raise PiperRuntimeError(
                "dependency_missing", "piper-plus package is not installed"
            ) from exc
        except PiperRuntimeError:
            raise
        except Exception as exc:
            raise PiperRuntimeError("model_invalid", str(exc)) from exc


class PiperPlusAdapter(EngineAdapter, AnnotatedSynthesisCapable):
    """Piper Plus engine adapter with runtime caching."""

    engine_id = "piper-plus"
    accepted_voice_kinds = frozenset({"model-file"})

    def __init__(
        self,
        synthesizer: PiperSynthesizer | None = None,
        *,
        runtime_cache: PiperRuntimeCache | None = None,
        config_reader: PiperConfigReader | None = None,
    ) -> None:
        self._cancelled_requests: set[str] = set()
        self._synthesizer = synthesizer or _default_piper_synthesizer
        self._runtime_cache = runtime_cache or PiperRuntimeCache()
        self._config_reader = config_reader or PiperConfigReader()
        self._resolved_voices: dict[str, ResolvedVoice] = {}

    @property
    def cancelled_requests(self) -> frozenset[str]:
        return frozenset(self._cancelled_requests)

    @property
    def runtime_cache(self) -> PiperRuntimeCache:
        return self._runtime_cache

    def register_resolved_voice(self, resolved: ResolvedVoice) -> None:
        """Register a resolved voice for runtime caching."""
        self._resolved_voices[resolved.voice_id] = resolved

    def health(self) -> str:
        if (
            importlib.util.find_spec("piper") is None
            and self._synthesizer is _default_piper_synthesizer
        ):
            return "dependency_missing: piper-plus package is not installed"
        return "available"

    def streaming_capability(self) -> StreamingCapabilityInfo:
        if importlib.util.find_spec("piper") is None:
            return StreamingCapabilityInfo(
                supported=False,
                mode=StreamingCapability.NOT_SUPPORTED,
            )
        return self._baseline_streaming_capability()

    def _baseline_streaming_capability(self) -> StreamingCapabilityInfo:
        return StreamingCapabilityInfo(
            supported=True,
            mode=StreamingCapability.SENTENCE_CHUNKED,
            granularity="sentence",
            true_incremental=False,
            format="pcm_s16le",
            sample_rates_hz=(22_050, 24_000),
        )

    def voice_streaming_capability(self, voice: VoiceDescriptor) -> StreamingCapabilityInfo:
        baseline = self._baseline_streaming_capability()
        if not baseline.supported:
            return baseline
        resolved = self._resolved_voices.get(voice.voice_id)
        if resolved is None:
            return baseline
        if not isinstance(resolved.payload, ResolvedModelFilePayload):
            return baseline
        native_rate = self._resolve_native_rate(resolved.payload)
        if native_rate is None:
            return baseline
        return replace(baseline, sample_rates_hz=(native_rate,))

    def _resolve_native_rate(self, payload: ResolvedModelFilePayload) -> int | None:
        if payload.native_sample_rate_hz is not None:
            return payload.native_sample_rate_hz
        if payload.config_path is None:
            return None
        return self._config_reader.read_sample_rate_hz(payload.config_path)

    def cancel(self, request_id: str) -> None:
        self._cancelled_requests.add(request_id)

    async def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)

        resolved = self._resolved_voices.get(voice.voice_id)
        sample_rate_hz = self._synthesis_sample_rate_hz(resolved)

        if resolved is not None:
            try:
                runtime = self._runtime_cache.get_or_load(voice.voice_id, resolved)
                chunks = await asyncio.to_thread(
                    lambda: list(self._synthesize_with_runtime(text, runtime))
                )
            except PiperRuntimeError as exc:
                raise RuntimeError(f"{exc.kind}: {exc.message}") from exc
        else:
            try:
                chunks = await asyncio.to_thread(lambda: list(self._synthesizer(text, voice)))
            except PiperRuntimeError as exc:
                raise RuntimeError(f"{exc.kind}: {exc.message}") from exc

        for pcm in chunks:
            if request_id is not None and request_id in self._cancelled_requests:
                break
            if voice.voice_id in self._cancelled_requests or "*" in self._cancelled_requests:
                break
            yield PCMChunk(
                pcm=pcm,
                sample_rate_hz=sample_rate_hz,
                channels=1,
                sample_width_bytes=2,
                encoding="pcm_s16le",
            )

    def _synthesis_sample_rate_hz(self, resolved: ResolvedVoice | None) -> int:
        if resolved is not None and isinstance(resolved.payload, ResolvedModelFilePayload):
            native = self._resolve_native_rate(resolved.payload)
            if native is not None:
                return native
        return _DEFAULT_SYNTHESIS_SAMPLE_RATE_HZ

    async def synthesize_annotated(
        self,
        text: str,
        voice: VoiceDescriptor,
    ) -> AnnotatedSynthesisResult:
        self.ensure_voice_supported(voice)
        resolved = self._resolved_voices.get(voice.voice_id)
        if resolved is None:
            raise RuntimeError("model_missing: voice not resolved")
        sample_rate = self._synthesis_sample_rate_hz(resolved)
        try:
            runtime = self._runtime_cache.get_or_load(voice.voice_id, resolved)
            session = PiperTimedSession(runtime, sample_rate=sample_rate)
            result = await asyncio.to_thread(session.synthesize_annotated, text)
        except PiperRuntimeError as exc:
            raise RuntimeError(f"{exc.kind}: {exc.message}") from exc
        return result

    def _synthesize_with_runtime(self, text: str, runtime: object) -> Iterable[bytes]:
        try:
            if hasattr(runtime, "synthesize_stream_raw"):
                raw_runtime = cast(_PiperRawStreamVoice, runtime)
                stream = raw_runtime.synthesize_stream_raw(text)
                return list(stream)
            typed_runtime = cast(_PiperVoice, runtime)
            return [chunk.audio_int16_bytes for chunk in typed_runtime.synthesize(text)]
        except Exception as exc:
            raise PiperRuntimeError("synthesis_failed", str(exc)) from exc

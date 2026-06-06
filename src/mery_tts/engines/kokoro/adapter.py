"""Kokoro engine adapter with runtime caching.

ADR-0024: Kokoro adapter lazy-loads runtime objects and caches them per installed
voice/artifact. It accepts resolved preset voices and emits normalized PCMChunk values.
"""

from __future__ import annotations

import asyncio
import importlib.util
from collections.abc import AsyncIterator, Callable, Iterable
from typing import Any

from mery_tts.engines.base import EngineAdapter, PCMChunk
from mery_tts.voice import PresetVoicePayload, VoiceDescriptor
from mery_tts.voice.resolver import ResolvedPresetPayload, ResolvedVoice

KokoroSynthesizer = Callable[[str, VoiceDescriptor], Iterable[bytes]]


class KokoroRuntimeError(Exception):
    """Structured Kokoro runtime error."""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message


def _default_kokoro_synthesizer(text: str, voice: VoiceDescriptor) -> Iterable[bytes]:
    if (
        importlib.util.find_spec("kokoro") is None
        and importlib.util.find_spec("kokoro_onnx") is None
    ):
        raise KokoroRuntimeError(
            "dependency_missing", "kokoro package is not installed"
        )
    if not isinstance(voice.payload, PresetVoicePayload):
        raise KokoroRuntimeError(
            "model_missing", "kokoro requires a preset voice payload"
        )
    raise KokoroRuntimeError(
        "model_missing", "kokoro pipeline loading is not configured for this voice"
    )


class KokoroRuntimeCache:
    """Lazy-loading runtime cache for Kokoro synthesizer instances."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    def get_or_load(self, voice_id: str, resolved: ResolvedVoice) -> Any:
        if voice_id in self._cache:
            return self._cache[voice_id]
        runtime = self._load_runtime(resolved)
        self._cache[voice_id] = runtime
        return runtime

    def invalidate(self, voice_id: str) -> None:
        self._cache.pop(voice_id, None)

    def clear(self) -> None:
        self._cache.clear()

    def _load_runtime(self, resolved: ResolvedVoice) -> Any:
        if not isinstance(resolved.payload, ResolvedPresetPayload):
            raise KokoroRuntimeError(
                "model_missing", "kokoro requires a resolved preset payload"
            )
        has_kokoro = importlib.util.find_spec("kokoro") is not None
        has_kokoro_onnx = importlib.util.find_spec("kokoro_onnx") is not None
        if not (has_kokoro or has_kokoro_onnx):
            raise KokoroRuntimeError(
                "dependency_missing", "kokoro package is not installed"
            )
        try:
            if has_kokoro_onnx:
                from kokoro_onnx import Kokoro  # type: ignore[import-untyped]

                model_path = str(resolved.payload.artifact_dir / "model.onnx")
                voices_path = str(resolved.payload.artifact_dir / "voices.bin")
                runtime = Kokoro(model_path, voices_path)
            else:
                import kokoro  # type: ignore[import-untyped]

                runtime = kokoro.Kokoro(str(resolved.payload.artifact_dir))
            return runtime
        except KokoroRuntimeError:
            raise
        except ImportError:
            raise KokoroRuntimeError(
                "dependency_missing", "kokoro package is not installed"
            )
        except Exception as exc:
            raise KokoroRuntimeError("model_invalid", str(exc)) from exc


class KokoroAdapter(EngineAdapter):
    """Kokoro engine adapter with runtime caching."""

    engine_id = "kokoro"
    accepted_voice_kinds = frozenset({"preset"})

    def __init__(
        self,
        synthesizer: KokoroSynthesizer | None = None,
        *,
        runtime_cache: KokoroRuntimeCache | None = None,
    ) -> None:
        self._cancelled_requests: set[str] = set()
        self._synthesizer = synthesizer or _default_kokoro_synthesizer
        self._runtime_cache = runtime_cache or KokoroRuntimeCache()
        self._resolved_voices: dict[str, ResolvedVoice] = {}

    @property
    def cancelled_requests(self) -> frozenset[str]:
        return frozenset(self._cancelled_requests)

    @property
    def runtime_cache(self) -> KokoroRuntimeCache:
        return self._runtime_cache

    def register_resolved_voice(self, resolved: ResolvedVoice) -> None:
        """Register a resolved voice for runtime caching."""
        self._resolved_voices[resolved.voice_id] = resolved

    def health(self) -> str:
        has_kokoro = importlib.util.find_spec("kokoro") is not None
        has_kokoro_onnx = importlib.util.find_spec("kokoro_onnx") is not None
        if not (has_kokoro or has_kokoro_onnx) and self._synthesizer is _default_kokoro_synthesizer:
            return "dependency_missing: kokoro package is not installed"
        return "available"

    def cancel(self, request_id: str) -> None:
        self._cancelled_requests.add(request_id)

    async def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)

        resolved = self._resolved_voices.get(voice.voice_id)
        if resolved is not None:
            try:
                runtime = self._runtime_cache.get_or_load(voice.voice_id, resolved)
                chunks = await asyncio.to_thread(
                    lambda: list(self._synthesize_with_runtime(text, runtime, voice))
                )
            except KokoroRuntimeError as exc:
                raise RuntimeError(f"{exc.kind}: {exc.message}") from exc
        else:
            try:
                chunks = await asyncio.to_thread(lambda: list(self._synthesizer(text, voice)))
            except KokoroRuntimeError as exc:
                raise RuntimeError(f"{exc.kind}: {exc.message}") from exc

        for pcm in chunks:
            if voice.voice_id in self._cancelled_requests or "*" in self._cancelled_requests:
                break
            yield PCMChunk(pcm=pcm, sample_rate_hz=24_000, channels=1)

    def _synthesize_with_runtime(
        self, text: str, runtime: Any, voice: VoiceDescriptor
    ) -> Iterable[bytes]:
        try:
            preset_id = voice.payload.preset_id if isinstance(voice.payload, PresetVoicePayload) else "default"
            result = runtime.synthesize(text, voice=preset_id)
            if hasattr(result, "__iter__") and not isinstance(result, (bytes, str)):
                return result
            return [result]
        except KokoroRuntimeError:
            raise
        except Exception as exc:
            raise KokoroRuntimeError("synthesis_failed", str(exc)) from exc

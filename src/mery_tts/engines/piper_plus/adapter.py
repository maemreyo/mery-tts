"""Piper Plus engine adapter with runtime caching.

ADR-0024: Piper adapter lazy-loads runtime objects and caches them per installed
voice/artifact. It accepts resolved model-file voices and emits normalized PCMChunk values.
"""

from __future__ import annotations

import asyncio
import importlib.util
from collections.abc import AsyncIterator, Callable, Iterable
from typing import Any, Protocol, cast

from mery_tts.engines.base import EngineAdapter, PCMChunk
from mery_tts.voice import ModelFileVoicePayload, VoiceDescriptor
from mery_tts.voice.resolver import ResolvedModelFilePayload, ResolvedVoice

PiperSynthesizer = Callable[[str, VoiceDescriptor], Iterable[bytes]]


class _PiperRuntime(Protocol):
    """Structural type for the optional piper-plus runtime objects."""

    def synthesize(self, text: str, /, *args: object, **kwargs: object) -> object: ...


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


class PiperRuntimeCache:
    """Lazy-loading runtime cache for Piper synthesizer instances."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    def get_or_load(self, voice_id: str, resolved: ResolvedVoice) -> _PiperRuntime:
        if voice_id in self._cache:
            return self._cache[voice_id]  # type: ignore[no-any-return]
        runtime = self._load_runtime(resolved)
        self._cache[voice_id] = runtime
        return runtime

    def invalidate(self, voice_id: str) -> None:
        self._cache.pop(voice_id, None)

    def clear(self) -> None:
        self._cache.clear()

    def _load_runtime(self, resolved: ResolvedVoice) -> _PiperRuntime:
        if not isinstance(resolved.payload, ResolvedModelFilePayload):
            raise PiperRuntimeError(
                "model_missing", "piper-plus requires a resolved model-file payload"
            )
        if importlib.util.find_spec("piper") is None:
            raise PiperRuntimeError("dependency_missing", "piper-plus package is not installed")
        try:
            import piper  # type: ignore[import-not-found]

            model_path = str(resolved.payload.model_path)
            config_path = (
                str(resolved.payload.config_path) if resolved.payload.config_path else None
            )
            voice_config = piper.PiperConfig.load(config_path) if config_path else None  # pyright: ignore[reportAttributeAccessIssue]
            synthesizer = piper.PiperSynthesizer(model_path, voice_config)  # pyright: ignore[reportAttributeAccessIssue]
            return synthesizer  # type: ignore[no-any-return]
        except ImportError as exc:
            raise PiperRuntimeError(
                "dependency_missing", "piper-plus package is not installed"
            ) from exc
        except PiperRuntimeError:
            raise
        except Exception as exc:
            raise PiperRuntimeError("model_invalid", str(exc)) from exc


class PiperPlusAdapter(EngineAdapter):
    """Piper Plus engine adapter with runtime caching."""

    engine_id = "piper-plus"
    accepted_voice_kinds = frozenset({"model-file"})

    def __init__(
        self,
        synthesizer: PiperSynthesizer | None = None,
        *,
        runtime_cache: PiperRuntimeCache | None = None,
    ) -> None:
        self._cancelled_requests: set[str] = set()
        self._synthesizer = synthesizer or _default_piper_synthesizer
        self._runtime_cache = runtime_cache or PiperRuntimeCache()
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

    def cancel(self, request_id: str) -> None:
        self._cancelled_requests.add(request_id)

    async def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)

        resolved = self._resolved_voices.get(voice.voice_id)
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
            if voice.voice_id in self._cancelled_requests or "*" in self._cancelled_requests:
                break
            yield PCMChunk(pcm=pcm, sample_rate_hz=24_000, channels=1)

    def _synthesize_with_runtime(self, text: str, runtime: _PiperRuntime) -> Iterable[bytes]:
        try:
            return cast("Iterable[bytes]", runtime.synthesize(text))
        except Exception as exc:
            raise PiperRuntimeError("synthesis_failed", str(exc)) from exc

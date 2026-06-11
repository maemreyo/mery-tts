"""SpeechSynthesisService — shared synthesis orchestration.

ADR-0022: All synthesis entry points (REST, CLI, smoke, console, future WS) route through
this service. Transports adapt inputs/outputs; the service owns voice plan resolution,
adapter calls, fallback, and synthesis diagnostics.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast
from uuid import uuid4

from mery_tts.engines.base import PCMChunk
from mery_tts.governance import is_gated_voice_risk_class
from mery_tts.text_normalization import normalize_text_for_locale
from mery_tts.voice.descriptor import VoiceDescriptor
from mery_tts.voice.registry import VoiceRegistry


class SynthesisErrorKind(StrEnum):
    """Classification of synthesis failures for fallback decisions."""

    UNKNOWN_VOICE = "unknown_voice"
    UNSUPPORTED_MODEL = "unsupported_model"
    UNSUPPORTED_FORMAT = "unsupported_format"
    ADAPTER_FAILURE = "adapter_failure"
    DEPENDENCY_MISSING = "dependency_missing"
    MODEL_MISSING = "model_missing"
    TEXT_TOO_LONG = "text_too_long"
    CANCELLED = "cancelled"
    AUTH_FAILURE = "auth_failure"
    CONTRACT_INCOMPATIBLE = "contract_incompatible"
    LOCALE_MISMATCH = "locale_mismatch"
    GATED_FEATURE = "gated_feature"
    NETWORK_DISABLED = "network_disabled"
    PROVIDER_BUSY = "provider_busy"
    TIMEOUT = "timeout"


class FallbackPolicy(StrEnum):
    """Fallback policy for synthesis requests."""

    AUTO = "auto"
    DISABLED = "disabled"


NON_RECOVERABLE_KINDS = frozenset(
    {
        SynthesisErrorKind.UNKNOWN_VOICE,
        SynthesisErrorKind.UNSUPPORTED_FORMAT,
        SynthesisErrorKind.TEXT_TOO_LONG,
        SynthesisErrorKind.CANCELLED,
        SynthesisErrorKind.AUTH_FAILURE,
        SynthesisErrorKind.CONTRACT_INCOMPATIBLE,
        SynthesisErrorKind.LOCALE_MISMATCH,
        SynthesisErrorKind.GATED_FEATURE,
        SynthesisErrorKind.NETWORK_DISABLED,
        SynthesisErrorKind.PROVIDER_BUSY,
        SynthesisErrorKind.TIMEOUT,
    }
)


class SynthesisError(Exception):
    """Structured synthesis error with kind classification for fallback decisions."""

    def __init__(
        self,
        kind: SynthesisErrorKind,
        message: str,
        *,
        voice_id: str | None = None,
        engine_id: str | None = None,
        diagnostic: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.voice_id = voice_id
        self.engine_id = engine_id
        self.diagnostic = diagnostic or {}

    @property
    def is_recoverable(self) -> bool:
        return self.kind not in NON_RECOVERABLE_KINDS


@dataclass(frozen=True, slots=True)
class VoiceAttempt:
    """Record of a single voice synthesis attempt."""

    voice_id: str
    engine_id: str
    success: bool
    error_kind: SynthesisErrorKind | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class AudioMetadata:
    """Audio metadata from a successful synthesis."""

    encoding: str
    sample_rate_hz: int
    channels: int
    duration_ms: int | None = None


@dataclass(frozen=True, slots=True)
class SynthesisDiagnostics:
    """Sanitized diagnostics from a synthesis operation."""

    request_id: str
    selected_voice_id: str
    selected_engine_id: str
    fallback_used: bool
    primary_voice_id: str | None = None
    fallback_voice_id: str | None = None
    fallback_reason: str | None = None
    attempts: tuple[VoiceAttempt, ...] = ()
    requested_locale: str | None = None
    selected_voice_locale: str | None = None
    normalization_diagnostics: dict[str, str | int] | None = None


@dataclass(frozen=True, slots=True)
class SynthesisResult:
    """Transport-neutral synthesis result."""

    chunks: tuple[PCMChunk, ...]
    audio_metadata: AudioMetadata
    diagnostics: SynthesisDiagnostics


@dataclass(frozen=True, slots=True)
class VoiceFallbackPlan:
    """Ordered fallback plan for synthesis."""

    primary_voice_id: str
    fallback_voice_ids: tuple[str, ...] = ()
    fallback_policy: FallbackPolicy = FallbackPolicy.AUTO

    @property
    def ordered_voice_ids(self) -> tuple[str, ...]:
        if self.fallback_policy == FallbackPolicy.DISABLED:
            return (self.primary_voice_id,)
        return (self.primary_voice_id, *self.fallback_voice_ids)


@dataclass(frozen=True, slots=True)
class MeryRequestOptions:
    """Mery-specific request options (namespaced under 'mery' in OpenAI-compatible requests)."""

    fallback_voice_ids: tuple[str, ...] = ()
    fallback_policy: FallbackPolicy = FallbackPolicy.AUTO
    diagnostics: str = "headers"
    requested_locale: str | None = None
    timeout_seconds: float | None = None


class VoicePlanResolver:
    """Resolves fallback plans from request options, config, and installed voices."""

    def __init__(
        self,
        *,
        voice_registry: VoiceRegistry,
        config_defaults: dict[str, Any] | None = None,
    ) -> None:
        self._registry = voice_registry
        self._config = config_defaults or {}

    def resolve(
        self,
        requested_voice: str,
        *,
        mery_options: MeryRequestOptions | None = None,
    ) -> VoiceFallbackPlan:
        options = mery_options or MeryRequestOptions()
        fallback_ids = options.fallback_voice_ids
        policy = options.fallback_policy

        if not fallback_ids and policy == FallbackPolicy.AUTO:
            config_fallback = self._config.get("fallbackVoiceIds", [])
            if isinstance(config_fallback, list):
                fallback_ids = tuple(config_fallback)
            config_policy = self._config.get("fallbackPolicy")
            if config_policy == "disabled":
                policy = FallbackPolicy.DISABLED

        return VoiceFallbackPlan(
            primary_voice_id=requested_voice,
            fallback_voice_ids=fallback_ids,
            fallback_policy=policy,
        )


class ProviderResourceLimiter:
    def __init__(
        self,
        *,
        concurrency_limits: dict[str, int] | None = None,
        queue_limits: dict[str, int] | None = None,
    ) -> None:
        self._concurrency_limits = concurrency_limits or {}
        self._queue_limits = queue_limits or {}
        self._active: dict[str, int] = {}
        self._queued: dict[str, int] = {}
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def acquire(self, provider_id: str) -> AsyncIterator[None]:
        limit = self._concurrency_limits.get(provider_id)
        if limit is None or limit <= 0:
            yield
            return
        async with self._lock:
            active = self._active.get(provider_id, 0)
            if active >= limit:
                queued = self._queued.get(provider_id, 0)
                queue_limit = self._queue_limits.get(provider_id, 0)
                if queued >= queue_limit:
                    raise SynthesisError(
                        kind=SynthesisErrorKind.PROVIDER_BUSY,
                        message="provider_busy",
                        engine_id=provider_id,
                        diagnostic={"reason": "provider_busy", "provider_id": provider_id},
                    )
                self._queued[provider_id] = queued + 1
                raise SynthesisError(
                    kind=SynthesisErrorKind.PROVIDER_BUSY,
                    message="provider_busy",
                    engine_id=provider_id,
                    diagnostic={"reason": "provider_busy", "provider_id": provider_id},
                )
            self._active[provider_id] = active + 1
        try:
            yield
        finally:
            async with self._lock:
                remaining = self._active.get(provider_id, 0) - 1
                if remaining > 0:
                    self._active[provider_id] = remaining
                else:
                    self._active.pop(provider_id, None)


class SpeechSynthesisService:
    """Shared synthesis orchestration service.

    All transports route through this service for voice plan resolution, adapter calls,
    fallback, and diagnostics.
    """

    def __init__(
        self,
        *,
        voice_registry: VoiceRegistry,
        voice_aliases: dict[str, str] | None = None,
        plan_resolver: VoicePlanResolver | None = None,
        purpose: str = "user",
        provider_network_policy: dict[str, str] | None = None,
        local_only: bool = False,
        air_gapped: bool = False,
        provider_concurrency_limits: dict[str, int] | None = None,
        provider_queue_limits: dict[str, int] | None = None,
        default_timeout_seconds: float | None = None,
        provider_timeout_overrides: dict[str, float] | None = None,
    ) -> None:
        self._registry = voice_registry
        self._aliases = voice_aliases or {}
        self._plan_resolver = plan_resolver or VoicePlanResolver(
            voice_registry=voice_registry,
        )
        self._purpose = purpose
        self._provider_network_policy = provider_network_policy or {}
        self._local_only = local_only
        self._air_gapped = air_gapped
        self._resource_limiter = ProviderResourceLimiter(
            concurrency_limits=provider_concurrency_limits,
            queue_limits=provider_queue_limits,
        )
        self._default_timeout_seconds = default_timeout_seconds
        self._provider_timeout_overrides = provider_timeout_overrides or {}
        self._last_request_id: str | None = None

    @property
    def purpose(self) -> str:
        return self._purpose

    def _resolve_native_voice_id(self, requested_voice: str) -> str:
        return self._aliases.get(requested_voice, requested_voice)

    async def synthesize(
        self,
        *,
        text: str,
        requested_voice: str,
        response_format: str = "pcm",
        mery_options: MeryRequestOptions | None = None,
    ) -> SynthesisResult:
        if response_format not in {"pcm", "wav"}:
            raise SynthesisError(
                kind=SynthesisErrorKind.UNSUPPORTED_FORMAT,
                message=f"unsupported response_format: {response_format}",
            )

        native_voice_id = self._resolve_native_voice_id(requested_voice)
        mery_options = mery_options or MeryRequestOptions()
        plan = self._plan_resolver.resolve(native_voice_id, mery_options=mery_options)
        request_id = f"req-{uuid4().hex[:12]}"
        self._last_request_id = request_id

        attempts: list[VoiceAttempt] = []
        last_error: SynthesisError | None = None

        for voice_id in plan.ordered_voice_ids:
            try:
                try:
                    _, selected_voice = self._registry.resolve_route(voice_id)
                except KeyError as exc:
                    raise SynthesisError(
                        kind=SynthesisErrorKind.UNKNOWN_VOICE,
                        message=f"voice '{voice_id}' is not installed",
                        voice_id=voice_id,
                    ) from exc
                selected_voice_locale = self._selected_voice_locale(selected_voice)
                self._ensure_high_risk_voice_not_gated(selected_voice)
                self._ensure_provider_network_allowed(selected_voice)
                self._ensure_locale_matches(
                    requested_locale=mery_options.requested_locale,
                    voice=selected_voice,
                    selected_voice_locale=selected_voice_locale,
                )
                normalized = normalize_text_for_locale(
                    text,
                    locale=mery_options.requested_locale or selected_voice_locale or "en-US",
                )
                synthesis_segments = self._synthesis_segments_for_locale(
                    normalized.text,
                    normalized.locale,
                    normalized.segments,
                )
                async with self._resource_limiter.acquire(selected_voice.engine_id):
                    chunks = await self._try_synthesize_segments_with_timeout(
                        synthesis_segments,
                        voice_id,
                        provider_id=selected_voice.engine_id,
                        requested_timeout_seconds=mery_options.timeout_seconds,
                    )
                if not chunks:
                    raise SynthesisError(
                        kind=SynthesisErrorKind.ADAPTER_FAILURE,
                        message="empty synthesis result",
                        voice_id=voice_id,
                    )
                metadata = self._extract_metadata(chunks, response_format)
                is_fallback = voice_id != plan.primary_voice_id
                diagnostics = self._build_diagnostics(
                    request_id=request_id,
                    plan=plan,
                    selected_voice_id=voice_id,
                    selected_engine_id=selected_voice.engine_id,
                    fallback_used=is_fallback,
                    fallback_reason=last_error.message if is_fallback and last_error else None,
                    attempts=tuple(attempts),
                    chunks=chunks,
                    requested_locale=mery_options.requested_locale,
                    selected_voice_locale=selected_voice_locale,
                    normalization_diagnostics=normalized.diagnostics(),
                )
                attempts.append(
                    VoiceAttempt(
                        voice_id=voice_id,
                        engine_id=diagnostics.selected_engine_id,
                        success=True,
                    )
                )
                return SynthesisResult(
                    chunks=tuple(chunks),
                    audio_metadata=metadata,
                    diagnostics=diagnostics,
                )
            except SynthesisError as exc:
                attempts.append(
                    VoiceAttempt(
                        voice_id=voice_id,
                        engine_id=exc.engine_id or self._engine_for_voice(voice_id),
                        success=False,
                        error_kind=exc.kind,
                        error_message=exc.message,
                    )
                )
                last_error = exc
                if not exc.is_recoverable:
                    raise
                continue

        raise last_error or SynthesisError(
            kind=SynthesisErrorKind.UNKNOWN_VOICE,
            message="no voices available for synthesis",
        )

    def _selected_voice_locale(self, voice: VoiceDescriptor) -> str | None:
        supported_locales = cast("Sequence[str]", getattr(voice, "supported_locales", []))
        if supported_locales:
            return supported_locales[0]
        return None

    def _synthesis_segments_for_locale(
        self,
        text: str,
        locale: str,
        normalized_segments: Sequence[str],
    ) -> tuple[str, ...]:
        if locale.startswith("vi-"):
            return (text,)
        return tuple(normalized_segments)

    def _ensure_high_risk_voice_not_gated(self, voice: VoiceDescriptor) -> None:
        if not is_gated_voice_risk_class(voice.risk_class):
            return
        raise SynthesisError(
            kind=SynthesisErrorKind.GATED_FEATURE,
            message="gated_feature",
            voice_id=voice.voice_id,
            engine_id=voice.engine_id,
            diagnostic={
                "reason": "gated_feature",
                "voice_id": voice.voice_id,
                "risk_class": voice.risk_class,
            },
        )

    def _ensure_provider_network_allowed(self, voice: VoiceDescriptor) -> None:
        if self._provider_network_policy.get(voice.engine_id) != "remote":
            return
        if not self._local_only and not self._air_gapped:
            return
        policy = "air_gapped" if self._air_gapped else "local_only"
        raise SynthesisError(
            kind=SynthesisErrorKind.NETWORK_DISABLED,
            message=f"network_disabled:{policy}:remote_provider",
            voice_id=voice.voice_id,
            engine_id=voice.engine_id,
            diagnostic={
                "reason": "network_disabled",
                "policy": policy,
                "operation": "remote_provider",
                "provider_id": voice.engine_id,
            },
        )

    def _ensure_locale_matches(
        self,
        *,
        requested_locale: str | None,
        voice: VoiceDescriptor,
        selected_voice_locale: str | None,
    ) -> None:
        if requested_locale is None:
            return
        supported_locales = getattr(voice, "supported_locales", [])
        if not supported_locales or requested_locale in supported_locales:
            return
        raise SynthesisError(
            kind=SynthesisErrorKind.LOCALE_MISMATCH,
            message="locale_mismatch",
            voice_id=voice.voice_id,
            engine_id=voice.engine_id,
            diagnostic={
                "reason": "locale_mismatch",
                "requested_locale": requested_locale,
                "selected_voice_locale": selected_voice_locale or "unknown",
                "voice_id": voice.voice_id,
            },
        )

    async def _try_synthesize_segments_with_timeout(
        self,
        segments: Sequence[str],
        voice_id: str,
        *,
        provider_id: str,
        requested_timeout_seconds: float | None,
    ) -> list[PCMChunk]:
        timeout_seconds = self._effective_timeout_seconds(
            provider_id=provider_id,
            requested_timeout_seconds=requested_timeout_seconds,
        )
        if timeout_seconds is None:
            return await self._try_synthesize_segments(segments, voice_id)
        try:
            return await asyncio.wait_for(
                self._try_synthesize_segments(segments, voice_id),
                timeout_seconds,
            )
        except TimeoutError as exc:
            raise SynthesisError(
                kind=SynthesisErrorKind.TIMEOUT,
                message="synthesis_timeout",
                voice_id=voice_id,
                engine_id=provider_id,
                diagnostic={
                    "reason": "synthesis_timeout",
                    "provider_id": provider_id,
                    "timeout_seconds": timeout_seconds,
                },
            ) from exc

    def _effective_timeout_seconds(
        self,
        *,
        provider_id: str,
        requested_timeout_seconds: float | None,
    ) -> float | None:
        configured = self._provider_timeout_overrides.get(
            provider_id,
            self._default_timeout_seconds,
        )
        if configured is None:
            return requested_timeout_seconds
        if requested_timeout_seconds is None:
            return configured
        return min(configured, requested_timeout_seconds)

    async def _try_synthesize_segments(
        self,
        segments: Sequence[str],
        voice_id: str,
    ) -> list[PCMChunk]:
        chunks: list[PCMChunk] = []
        for segment in segments:
            chunks.extend(await self._try_synthesize(segment, voice_id))
        return chunks

    async def _try_synthesize(self, text: str, voice_id: str) -> list[PCMChunk]:
        try:
            adapter, voice = self._registry.resolve_route(voice_id)
        except KeyError:
            raise SynthesisError(
                kind=SynthesisErrorKind.UNKNOWN_VOICE,
                message=f"voice '{voice_id}' is not installed",
                voice_id=voice_id,
            ) from None

        try:
            chunks: list[PCMChunk] = []
            async for chunk in adapter.synthesize(text, voice, request_id=self._last_request_id):
                chunks.append(chunk)
            return chunks
        except RuntimeError as exc:
            error_msg = str(exc)
            kind = self._classify_runtime_error(error_msg)
            raise SynthesisError(
                kind=kind,
                message=error_msg,
                voice_id=voice_id,
                engine_id=voice.engine_id,
                diagnostic={"raw_error": error_msg},
            ) from exc

    def _classify_runtime_error(self, message: str) -> SynthesisErrorKind:
        if "dependency_missing" in message:
            return SynthesisErrorKind.DEPENDENCY_MISSING
        if "model_missing" in message:
            return SynthesisErrorKind.MODEL_MISSING
        return SynthesisErrorKind.ADAPTER_FAILURE

    def _engine_for_voice(self, voice_id: str) -> str:
        try:
            voice = self._registry.resolve(voice_id)
            return voice.engine_id
        except KeyError:
            return "unknown"

    def _extract_metadata(self, chunks: Sequence[PCMChunk], response_format: str) -> AudioMetadata:
        if not chunks:
            return AudioMetadata(
                encoding=response_format,
                sample_rate_hz=0,
                channels=0,
            )
        first = chunks[0]
        total_bytes = sum(len(c.pcm) for c in chunks)
        bytes_per_sample = 2 * first.channels
        duration_ms = (
            int(total_bytes / bytes_per_sample / first.sample_rate_hz * 1000)
            if bytes_per_sample > 0 and first.sample_rate_hz > 0
            else None
        )
        return AudioMetadata(
            encoding=response_format,
            sample_rate_hz=first.sample_rate_hz,
            channels=first.channels,
            duration_ms=duration_ms,
        )

    def _build_diagnostics(
        self,
        *,
        request_id: str,
        plan: VoiceFallbackPlan,
        selected_voice_id: str,
        selected_engine_id: str,
        fallback_used: bool,
        fallback_reason: str | None,
        attempts: tuple[VoiceAttempt, ...],
        chunks: Sequence[PCMChunk],
        requested_locale: str | None,
        selected_voice_locale: str | None,
        normalization_diagnostics: dict[str, str | int] | None,
    ) -> SynthesisDiagnostics:
        engine_id = selected_engine_id
        if chunks:
            try:
                _, voice = self._registry.resolve_route(selected_voice_id)
                engine_id = voice.engine_id
            except KeyError:
                pass

        return SynthesisDiagnostics(
            request_id=request_id,
            selected_voice_id=selected_voice_id,
            selected_engine_id=engine_id,
            fallback_used=fallback_used,
            primary_voice_id=plan.primary_voice_id,
            fallback_voice_id=selected_voice_id if fallback_used else None,
            fallback_reason=fallback_reason,
            attempts=attempts,
            requested_locale=requested_locale,
            selected_voice_locale=selected_voice_locale,
            normalization_diagnostics=normalization_diagnostics,
        )


__all__ = [
    "AudioMetadata",
    "FallbackPolicy",
    "MeryRequestOptions",
    "SpeechSynthesisService",
    "SynthesisDiagnostics",
    "SynthesisError",
    "SynthesisErrorKind",
    "SynthesisResult",
    "VoiceAttempt",
    "VoiceFallbackPlan",
    "VoicePlanResolver",
]

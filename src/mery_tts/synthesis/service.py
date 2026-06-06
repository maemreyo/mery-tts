"""SpeechSynthesisService — shared synthesis orchestration.

ADR-0022: All synthesis entry points (REST, CLI, smoke, console, future WS) route through
this service. Transports adapt inputs/outputs; the service owns voice plan resolution,
adapter calls, fallback, and synthesis diagnostics.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import uuid4

from mery_tts.engines.base import PCMChunk
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
    ) -> None:
        self._registry = voice_registry
        self._aliases = voice_aliases or {}
        self._plan_resolver = plan_resolver or VoicePlanResolver(
            voice_registry=voice_registry,
        )
        self._purpose = purpose
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
        plan = self._plan_resolver.resolve(native_voice_id, mery_options=mery_options)
        request_id = f"req-{uuid4().hex[:12]}"
        self._last_request_id = request_id

        attempts: list[VoiceAttempt] = []
        last_error: SynthesisError | None = None

        for voice_id in plan.ordered_voice_ids:
            try:
                chunks = await self._try_synthesize(text, voice_id)
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
                    selected_engine_id=chunks[0].__class__.__name__,
                    fallback_used=is_fallback,
                    fallback_reason=last_error.message if is_fallback and last_error else None,
                    attempts=tuple(attempts),
                    chunks=chunks,
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

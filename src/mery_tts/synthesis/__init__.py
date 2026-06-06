"""Shared synthesis orchestration."""

from .service import (
    AudioMetadata,
    FallbackPolicy,
    MeryRequestOptions,
    SpeechSynthesisService,
    SynthesisDiagnostics,
    SynthesisError,
    SynthesisErrorKind,
    SynthesisResult,
    VoiceAttempt,
    VoiceFallbackPlan,
    VoicePlanResolver,
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

from .factories import diagnostic_error, fallback_for, sanitize_diagnostic
from .taxonomy import (
    ErrorCategory,
    ErrorCode,
    ErrorRecoverability,
    ErrorSeverity,
    FallbackPolicy,
    LocalTTSError,
    RecommendedAction,
)

__all__ = [
    "ErrorCategory",
    "ErrorCode",
    "ErrorRecoverability",
    "ErrorSeverity",
    "FallbackPolicy",
    "LocalTTSError",
    "RecommendedAction",
    "diagnostic_error",
    "fallback_for",
    "sanitize_diagnostic",
]

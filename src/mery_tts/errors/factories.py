from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any

from mery_tts.errors.taxonomy import (
    ErrorCategory,
    ErrorCode,
    ErrorRecoverability,
    ErrorSeverity,
    FallbackPolicy,
    LocalTTSError,
    RecommendedAction,
)

ScalarDiagnostic = str | int | float | bool

FORBIDDEN_DIAGNOSTIC_KEYS = frozenset(
    {
        "api_key",
        "article_content",
        "page_url",
        "raw_engine_message",
        "raw_text",
        "text",
        "token",
        "url",
        "user_id",
    }
)


@dataclass(frozen=True, slots=True)
class ErrorPolicy:
    recommended_action: RecommendedAction
    fallback_policy: FallbackPolicy
    recoverability: ErrorRecoverability


HELP_TOPICS: dict[ErrorCode, str] = {
    ErrorCode.CONNECTION_DAEMON_UNREACHABLE: "provider-unavailable",
    ErrorCode.CONNECTION_TIMEOUT: "provider-unavailable",
    ErrorCode.CONNECTION_RATE_LIMITED: "provider-unavailable",
    ErrorCode.MODEL_NOT_INSTALLED: "model-corrupt-reinstall",
    ErrorCode.MODEL_INSTALL_FAILED: "model-corrupt-reinstall",
    ErrorCode.MODEL_DELETE_FAILED: "model-corrupt-reinstall",
    ErrorCode.CATALOG_SIGNATURE_INVALID: "catalog-invalid",
    ErrorCode.CATALOG_SCHEMA_INVALID: "catalog-invalid",
    ErrorCode.CATALOG_COMMUNITY_DISABLED: "catalog-invalid",
    ErrorCode.ENGINE_UNAVAILABLE: "provider-unavailable",
    ErrorCode.ENGINE_VOICE_UNSUPPORTED: "provider-unavailable",
    ErrorCode.SYNTHESIS_FAILED: "provider-unavailable",
    ErrorCode.PLAYBACK_DEVICE_UNAVAILABLE: "provider-unavailable",
    ErrorCode.STORAGE_MANIFEST_MISSING: "model-corrupt-reinstall",
    ErrorCode.STORAGE_WRITE_FAILED: "diagnostics-export",
    ErrorCode.UPDATE_CONFIRMATION_REQUIRED: "model-corrupt-reinstall",
    ErrorCode.AUTH_TOKEN_INVALID: "pairing-token",
    ErrorCode.AUTH_TOKEN_MISSING: "pairing-token",
    ErrorCode.AUTH_RATE_LIMITED: "pairing-token",
}


POLICIES: dict[ErrorCode, ErrorPolicy] = {
    ErrorCode.CONNECTION_DAEMON_UNREACHABLE: ErrorPolicy(
        recommended_action=RecommendedAction.RETRY,
        fallback_policy=FallbackPolicy.USE_CACHED_AUDIO,
        recoverability=ErrorRecoverability.RETRYABLE,
    ),
    ErrorCode.CONNECTION_TIMEOUT: ErrorPolicy(
        recommended_action=RecommendedAction.RETRY,
        fallback_policy=FallbackPolicy.USE_CACHED_AUDIO,
        recoverability=ErrorRecoverability.RETRYABLE,
    ),
    ErrorCode.CONNECTION_RATE_LIMITED: ErrorPolicy(
        recommended_action=RecommendedAction.RETRY,
        fallback_policy=FallbackPolicy.RETRY_WITH_BACKOFF,
        recoverability=ErrorRecoverability.RETRYABLE,
    ),
    ErrorCode.MODEL_NOT_INSTALLED: ErrorPolicy(
        recommended_action=RecommendedAction.INSTALL_MODEL,
        fallback_policy=FallbackPolicy.USE_DEFAULT_VOICE,
        recoverability=ErrorRecoverability.USER_ACTION,
    ),
    ErrorCode.MODEL_INSTALL_FAILED: ErrorPolicy(
        recommended_action=RecommendedAction.RETRY,
        fallback_policy=FallbackPolicy.RETRY_WITH_BACKOFF,
        recoverability=ErrorRecoverability.RETRYABLE,
    ),
    ErrorCode.MODEL_DELETE_FAILED: ErrorPolicy(
        recommended_action=RecommendedAction.RETRY,
        fallback_policy=FallbackPolicy.NONE,
        recoverability=ErrorRecoverability.RETRYABLE,
    ),
    ErrorCode.CATALOG_SIGNATURE_INVALID: ErrorPolicy(
        recommended_action=RecommendedAction.RETRY,
        fallback_policy=FallbackPolicy.USE_CACHED_AUDIO,
        recoverability=ErrorRecoverability.RETRYABLE,
    ),
    ErrorCode.CATALOG_SCHEMA_INVALID: ErrorPolicy(
        recommended_action=RecommendedAction.CONTACT_SUPPORT,
        fallback_policy=FallbackPolicy.DISABLE_FEATURE,
        recoverability=ErrorRecoverability.UNRECOVERABLE,
    ),
    ErrorCode.CATALOG_COMMUNITY_DISABLED: ErrorPolicy(
        recommended_action=RecommendedAction.NONE,
        fallback_policy=FallbackPolicy.DISABLE_FEATURE,
        recoverability=ErrorRecoverability.USER_ACTION,
    ),
    ErrorCode.ENGINE_UNAVAILABLE: ErrorPolicy(
        recommended_action=RecommendedAction.CHECK_ENGINE,
        fallback_policy=FallbackPolicy.USE_DEFAULT_VOICE,
        recoverability=ErrorRecoverability.CONFIGURATION,
    ),
    ErrorCode.ENGINE_VOICE_UNSUPPORTED: ErrorPolicy(
        recommended_action=RecommendedAction.INSTALL_MODEL,
        fallback_policy=FallbackPolicy.USE_DEFAULT_VOICE,
        recoverability=ErrorRecoverability.USER_ACTION,
    ),
    ErrorCode.SYNTHESIS_FAILED: ErrorPolicy(
        recommended_action=RecommendedAction.RETRY,
        fallback_policy=FallbackPolicy.USE_DEFAULT_VOICE,
        recoverability=ErrorRecoverability.RETRYABLE,
    ),
    ErrorCode.SYNTHESIS_UNSUPPORTED_FORMAT: ErrorPolicy(
        recommended_action=RecommendedAction.NONE,
        fallback_policy=FallbackPolicy.NONE,
        recoverability=ErrorRecoverability.UNRECOVERABLE,
    ),
    ErrorCode.SYNTHESIS_LOCALE_MISMATCH: ErrorPolicy(
        recommended_action=RecommendedAction.NONE,
        fallback_policy=FallbackPolicy.NONE,
        recoverability=ErrorRecoverability.USER_ACTION,
    ),
    ErrorCode.SYNTHESIS_GATED_FEATURE: ErrorPolicy(
        recommended_action=RecommendedAction.NONE,
        fallback_policy=FallbackPolicy.DISABLE_FEATURE,
        recoverability=ErrorRecoverability.USER_ACTION,
    ),
    ErrorCode.PLAYBACK_DEVICE_UNAVAILABLE: ErrorPolicy(
        recommended_action=RecommendedAction.CHECK_ENGINE,
        fallback_policy=FallbackPolicy.USE_CACHED_AUDIO,
        recoverability=ErrorRecoverability.CONFIGURATION,
    ),
    ErrorCode.STORAGE_MANIFEST_MISSING: ErrorPolicy(
        recommended_action=RecommendedAction.INSTALL_MODEL,
        fallback_policy=FallbackPolicy.USE_DEFAULT_VOICE,
        recoverability=ErrorRecoverability.USER_ACTION,
    ),
    ErrorCode.STORAGE_WRITE_FAILED: ErrorPolicy(
        recommended_action=RecommendedAction.FREE_SPACE,
        fallback_policy=FallbackPolicy.NONE,
        recoverability=ErrorRecoverability.USER_ACTION,
    ),
    ErrorCode.STORAGE_MODEL_CLEANUP_REFUSED: ErrorPolicy(
        recommended_action=RecommendedAction.NONE,
        fallback_policy=FallbackPolicy.NONE,
        recoverability=ErrorRecoverability.USER_ACTION,
    ),
    ErrorCode.UPDATE_CONFIRMATION_REQUIRED: ErrorPolicy(
        recommended_action=RecommendedAction.CONFIRM_UPDATE,
        fallback_policy=FallbackPolicy.NONE,
        recoverability=ErrorRecoverability.USER_ACTION,
    ),
    ErrorCode.AUTH_TOKEN_INVALID: ErrorPolicy(
        recommended_action=RecommendedAction.PAIR_CLIENT,
        fallback_policy=FallbackPolicy.NONE,
        recoverability=ErrorRecoverability.USER_ACTION,
    ),
    ErrorCode.AUTH_TOKEN_MISSING: ErrorPolicy(
        recommended_action=RecommendedAction.PAIR_CLIENT,
        fallback_policy=FallbackPolicy.NONE,
        recoverability=ErrorRecoverability.USER_ACTION,
    ),
    ErrorCode.AUTH_RATE_LIMITED: ErrorPolicy(
        recommended_action=RecommendedAction.RETRY,
        fallback_policy=FallbackPolicy.RETRY_WITH_BACKOFF,
        recoverability=ErrorRecoverability.RETRYABLE,
    ),
    ErrorCode.SECURITY_UNSAFE_IDENTIFIER: ErrorPolicy(
        recommended_action=RecommendedAction.NONE,
        fallback_policy=FallbackPolicy.NONE,
        recoverability=ErrorRecoverability.UNRECOVERABLE,
    ),
    ErrorCode.SECURITY_REQUEST_TOO_LARGE: ErrorPolicy(
        recommended_action=RecommendedAction.NONE,
        fallback_policy=FallbackPolicy.NONE,
        recoverability=ErrorRecoverability.UNRECOVERABLE,
    ),
}


def _is_suspicious_diagnostic_string(value: str) -> bool:
    lowered = value.lower()
    if any(marker in lowered for marker in ("http://", "https://", "file://")):
        return True
    if "traceback (most recent call last)" in lowered:
        return True
    if lowered.startswith("file ") and ", line " in lowered:
        return True
    if "bearer " in lowered or "api_key" in lowered or "token=" in lowered:
        return True
    if "/users/" in lowered or "\\users\\" in lowered:
        return True
    return PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute()


def sanitize_diagnostic(metadata: dict[str, Any]) -> dict[str, ScalarDiagnostic]:
    sanitized: dict[str, ScalarDiagnostic] = {}
    for key, value in metadata.items():
        normalized_key = key.lower()
        if normalized_key in FORBIDDEN_DIAGNOSTIC_KEYS:
            continue
        if isinstance(value, str):
            if _is_suspicious_diagnostic_string(value):
                continue
            sanitized[key] = value
            continue
        if isinstance(value, int | float | bool):
            sanitized[key] = value
    return sanitized


def fallback_for(code: ErrorCode) -> ErrorPolicy:
    return POLICIES.get(
        code,
        ErrorPolicy(
            recommended_action=RecommendedAction.CONTACT_SUPPORT,
            fallback_policy=FallbackPolicy.NONE,
            recoverability=ErrorRecoverability.UNRECOVERABLE,
        ),
    )


def diagnostic_error(
    *,
    code: ErrorCode,
    category: ErrorCategory,
    request_id: str,
    diagnostic: dict[str, Any],
) -> LocalTTSError:
    policy = fallback_for(code)
    sanitized = sanitize_diagnostic(diagnostic)
    diagnostic_text = ",".join(f"{key}={value}" for key, value in sorted(sanitized.items()))
    return LocalTTSError(
        code=code,
        category=category,
        severity=ErrorSeverity.ERROR,
        recoverability=policy.recoverability,
        user_message_key=f"errors.{code.value.replace('.', '_')}",
        recommended_action=policy.recommended_action,
        fallback_policy=policy.fallback_policy,
        help_topic=HELP_TOPICS.get(code),
        sanitized_diagnostic=diagnostic_text or "diagnostic omitted",
        request_id=request_id,
        timestamp=datetime.now(UTC),
    )

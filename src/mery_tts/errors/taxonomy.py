from datetime import datetime
from enum import StrEnum
from typing import Any


class ErrorCategory(StrEnum):
    CONNECTION = "connection"
    AUTH = "auth"
    CATALOG = "catalog"
    MODEL = "model"
    ENGINE = "engine"
    SYNTHESIS = "synthesis"
    PLAYBACK = "playback"
    STORAGE = "storage"
    SECURITY = "security"


class ErrorSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


class ErrorRecoverability(StrEnum):
    RETRYABLE = "retryable"
    USER_ACTION = "user_action"
    CONFIGURATION = "configuration"
    UNRECOVERABLE = "unrecoverable"


class RecommendedAction(StrEnum):
    NONE = "none"
    RETRY = "retry"
    PAIR_CLIENT = "pair_client"
    INSTALL_MODEL = "install_model"
    CHECK_ENGINE = "check_engine"
    FREE_SPACE = "free_space"
    CONTACT_SUPPORT = "contact_support"


class FallbackPolicy(StrEnum):
    NONE = "none"
    USE_DEFAULT_VOICE = "use_default_voice"
    USE_CACHED_AUDIO = "use_cached_audio"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    DISABLE_FEATURE = "disable_feature"


class ErrorCode(StrEnum):
    CONNECTION_DAEMON_UNREACHABLE = "connection.daemon_unreachable"
    CONNECTION_TIMEOUT = "connection.timeout"
    AUTH_TOKEN_MISSING = "auth.token_missing"
    AUTH_TOKEN_INVALID = "auth.token_invalid"
    CATALOG_SIGNATURE_INVALID = "catalog.signature_invalid"
    CATALOG_SCHEMA_INVALID = "catalog.schema_invalid"
    MODEL_DELETE_FAILED = "model.delete_failed"
    MODEL_INSTALL_FAILED = "model.install_failed"
    MODEL_NOT_INSTALLED = "model.not_installed"
    ENGINE_UNAVAILABLE = "engine.unavailable"
    ENGINE_VOICE_UNSUPPORTED = "engine.voice_unsupported"
    SYNTHESIS_FAILED = "synthesis.failed"
    SYNTHESIS_UNSUPPORTED_FORMAT = "synthesis.unsupported_format"
    PLAYBACK_DEVICE_UNAVAILABLE = "playback.device_unavailable"
    STORAGE_MANIFEST_MISSING = "storage.manifest_missing"
    STORAGE_WRITE_FAILED = "storage.write_failed"
    SECURITY_UNSAFE_IDENTIFIER = "security.unsafe_identifier"
    SECURITY_REQUEST_TOO_LARGE = "security.request_too_large"


class LocalTTSError(Exception):
    def __init__(
        self,
        *,
        code: ErrorCode,
        category: ErrorCategory,
        severity: ErrorSeverity,
        recoverability: ErrorRecoverability,
        user_message_key: str,
        recommended_action: RecommendedAction,
        fallback_policy: FallbackPolicy,
        sanitized_diagnostic: str,
        request_id: str,
        timestamp: datetime,
    ) -> None:
        self.code = code
        self.category = category
        self.severity = severity
        self.recoverability = recoverability
        self.user_message_key = user_message_key
        self.recommended_action = recommended_action
        self.fallback_policy = fallback_policy
        self.sanitized_diagnostic = sanitized_diagnostic
        self.request_id = request_id
        self.timestamp = timestamp
        super().__init__(f"{code.value}: {sanitized_diagnostic}")

    def model_dump(self, *, mode: str = "python") -> dict[str, Any]:
        timestamp: datetime | str = self.timestamp
        if mode == "json":
            timestamp = self.timestamp.isoformat().replace("+00:00", "Z")
        return {
            "code": self.code.value,
            "category": self.category.value,
            "severity": self.severity.value,
            "recoverability": self.recoverability.value,
            "user_message_key": self.user_message_key,
            "recommended_action": self.recommended_action.value,
            "fallback_policy": self.fallback_policy.value,
            "sanitized_diagnostic": self.sanitized_diagnostic,
            "request_id": self.request_id,
            "timestamp": timestamp,
        }

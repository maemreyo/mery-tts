from mery_tts.errors import (
    ErrorCategory,
    ErrorCode,
    FallbackPolicy,
    RecommendedAction,
)
from mery_tts.errors.factories import POLICIES, diagnostic_error, fallback_for, sanitize_diagnostic


def test_sanitizer_keeps_shallow_scalar_metadata() -> None:
    assert sanitize_diagnostic({"engine": "kokoro", "attempt": 2, "retryable": True}) == {
        "engine": "kokoro",
        "attempt": 2,
        "retryable": True,
    }


def test_sanitizer_drops_forbidden_and_nested_metadata() -> None:
    assert (
        sanitize_diagnostic(
            {
                "token": "secret",
                "raw_text": "private article",
                "page_url": "https://example.com/article",
                "nested": {"engine": "raw"},
            }
        )
        == {}
    )


def test_sanitizer_drops_suspicious_scalar_values() -> None:
    assert sanitize_diagnostic(
        {
            "engine": "kokoro",
            "path_hint": "/Users/me/.mery/model.onnx",
            "download_hint": "https://example.com/model.onnx",
            "error_hint": "Traceback (most recent call last): secret",
            "frame_hint": 'File "/app/engine.py", line 42, in synthesize',
            "exception_hint": "RuntimeError: failed to load /Users/me/model.onnx",
            "token_hint": "bearer abc123",
        }
    ) == {"engine": "kokoro"}


def test_engine_exception_translation_is_sanitized() -> None:
    error = diagnostic_error(
        code=ErrorCode.ENGINE_UNAVAILABLE,
        category=ErrorCategory.ENGINE,
        request_id="req",
        diagnostic={"engine": "kokoro", "raw_engine_message": "Traceback with /Users/me"},
    )

    assert error.sanitized_diagnostic == "engine=kokoro"


def test_fallback_policy_map_covers_representative_categories() -> None:
    connection = fallback_for(ErrorCode.CONNECTION_DAEMON_UNREACHABLE)
    catalog = fallback_for(ErrorCode.CATALOG_SIGNATURE_INVALID)
    model = fallback_for(ErrorCode.MODEL_NOT_INSTALLED)
    engine = fallback_for(ErrorCode.ENGINE_UNAVAILABLE)
    synthesis = fallback_for(ErrorCode.SYNTHESIS_FAILED)
    playback = fallback_for(ErrorCode.PLAYBACK_DEVICE_UNAVAILABLE)
    storage = fallback_for(ErrorCode.STORAGE_WRITE_FAILED)
    auth = fallback_for(ErrorCode.AUTH_TOKEN_INVALID)
    rate_limited = fallback_for(ErrorCode.AUTH_RATE_LIMITED)
    security = fallback_for(ErrorCode.SECURITY_UNSAFE_IDENTIFIER)

    assert connection.recommended_action == RecommendedAction.RETRY
    assert connection.fallback_policy == FallbackPolicy.USE_CACHED_AUDIO
    assert catalog.recommended_action == RecommendedAction.RETRY
    assert catalog.fallback_policy == FallbackPolicy.USE_CACHED_AUDIO
    assert model.recommended_action == RecommendedAction.INSTALL_MODEL
    assert model.fallback_policy == FallbackPolicy.USE_DEFAULT_VOICE
    assert engine.recommended_action == RecommendedAction.CHECK_ENGINE
    assert engine.fallback_policy == FallbackPolicy.USE_DEFAULT_VOICE
    assert synthesis.recommended_action == RecommendedAction.RETRY
    assert synthesis.fallback_policy == FallbackPolicy.USE_DEFAULT_VOICE
    assert playback.recommended_action == RecommendedAction.CHECK_ENGINE
    assert playback.fallback_policy == FallbackPolicy.USE_CACHED_AUDIO
    assert storage.recommended_action == RecommendedAction.FREE_SPACE
    assert storage.fallback_policy == FallbackPolicy.NONE
    assert auth.recommended_action == RecommendedAction.PAIR_CLIENT
    assert auth.fallback_policy == FallbackPolicy.NONE
    assert rate_limited.recommended_action == RecommendedAction.RETRY
    assert rate_limited.fallback_policy == FallbackPolicy.RETRY_WITH_BACKOFF
    assert security.recommended_action == RecommendedAction.NONE
    assert security.fallback_policy == FallbackPolicy.NONE


def test_every_declared_error_code_has_explicit_fallback_policy() -> None:
    assert set(POLICIES) == set(ErrorCode)

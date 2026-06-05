from mery_tts.errors import ErrorCategory, ErrorCode, FallbackPolicy, RecommendedAction
from mery_tts.errors.factories import diagnostic_error, fallback_for, sanitize_diagnostic


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
    model = fallback_for(ErrorCode.MODEL_NOT_INSTALLED)
    auth = fallback_for(ErrorCode.AUTH_TOKEN_INVALID)

    assert connection.recommended_action == RecommendedAction.RETRY
    assert connection.fallback_policy == FallbackPolicy.RETRY_WITH_BACKOFF
    assert model.recommended_action == RecommendedAction.INSTALL_MODEL
    assert auth.recommended_action == RecommendedAction.PAIR_CLIENT
    assert auth.fallback_policy == FallbackPolicy.NONE

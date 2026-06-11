from mery_tts.errors import (
    ErrorCategory,
    ErrorCode,
    ErrorRecoverability,
    FallbackPolicy,
    RecommendedAction,
)
from mery_tts.errors.factories import (
    HELP_TOPICS,
    POLICIES,
    diagnostic_error,
    fallback_for,
    sanitize_diagnostic,
)


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


def test_real_domain_error_diagnostics_are_sanitized() -> None:
    cases = [
        diagnostic_error(
            code=ErrorCode.MODEL_INSTALL_FAILED,
            category=ErrorCategory.MODEL,
            request_id="install",
            diagnostic={"phase": "download", "reason": "Traceback secret /Users/me/model.onnx"},
        ),
        diagnostic_error(
            code=ErrorCode.SYNTHESIS_FAILED,
            category=ErrorCategory.SYNTHESIS,
            request_id="synthesis",
            diagnostic={"voice": "alloy", "error": "RuntimeError secret /Users/me/voice.pt"},
        ),
        diagnostic_error(
            code=ErrorCode.STORAGE_WRITE_FAILED,
            category=ErrorCategory.STORAGE,
            request_id="doctor",
            diagnostic={"check": "doctor", "detail": "token=secret Traceback /Users/me"},
        ),
        diagnostic_error(
            code=ErrorCode.SECURITY_UNSAFE_IDENTIFIER,
            category=ErrorCategory.SECURITY,
            request_id="middleware",
            diagnostic={"reason": "origin_not_allowed", "origin": "https://evil.example/secret"},
        ),
    ]

    for error in cases:
        assert "secret" not in error.sanitized_diagnostic
        assert "/Users" not in error.sanitized_diagnostic
        assert "Traceback" not in error.sanitized_diagnostic


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


def test_connection_error_serializes_with_fallback_policy_metadata() -> None:
    error = diagnostic_error(
        code=ErrorCode.CONNECTION_DAEMON_UNREACHABLE,
        category=ErrorCategory.CONNECTION,
        request_id="req-connection",
        diagnostic={"host": "127.0.0.1", "port": 8765},
    )

    serialized = error.model_dump(mode="json")

    assert serialized["code"] == "connection.daemon_unreachable"
    assert serialized["fallback_policy"] == "use_cached_audio"
    assert serialized["recommended_action"] == "retry"
    assert serialized["request_id"] == "req-connection"


def test_every_declared_error_code_has_explicit_fallback_policy() -> None:
    assert set(POLICIES) == set(ErrorCode)


def test_every_error_category_has_at_least_one_error_code() -> None:
    from mery_tts.errors.taxonomy import ErrorCategory

    categories_in_codes = {code.split(".")[0] for code in ErrorCode}
    expected_categories = {category.value for category in ErrorCategory}

    assert categories_in_codes == expected_categories


def test_all_policies_use_valid_recommended_actions_and_fallback_policies() -> None:
    from mery_tts.errors.taxonomy import FallbackPolicy, RecommendedAction

    valid_actions = {action.value for action in RecommendedAction}
    valid_fallbacks = {policy.value for policy in FallbackPolicy}

    for code, policy in POLICIES.items():
        assert policy.recommended_action.value in valid_actions, (
            f"Policy for {code.value} has invalid recommended_action"
        )
        assert policy.fallback_policy.value in valid_fallbacks, (
            f"Policy for {code.value} has invalid fallback_policy"
        )


def test_all_policies_use_valid_recoverability_values() -> None:
    from mery_tts.errors.taxonomy import ErrorRecoverability

    valid_recoverability = {value.value for value in ErrorRecoverability}

    for code, policy in POLICIES.items():
        assert policy.recoverability.value in valid_recoverability, (
            f"Policy for {code.value} has invalid recoverability"
        )


def test_diagnostic_error_generates_correct_user_message_key() -> None:
    error = diagnostic_error(
        code=ErrorCode.AUTH_TOKEN_MISSING,
        category=ErrorCategory.AUTH,
        request_id="req-test",
        diagnostic={"reason": "missing"},
    )

    assert error.user_message_key == "errors.auth_token_missing"


def test_diagnostic_error_maps_code_to_correct_policy() -> None:
    error = diagnostic_error(
        code=ErrorCode.MODEL_NOT_INSTALLED,
        category=ErrorCategory.MODEL,
        request_id="req-test",
        diagnostic={"model_id": "test.model"},
    )

    assert error.recommended_action == RecommendedAction.INSTALL_MODEL
    assert error.fallback_policy == FallbackPolicy.USE_DEFAULT_VOICE
    assert error.recoverability == ErrorRecoverability.USER_ACTION
    assert error.help_topic == "model-corrupt-reinstall"


def test_user_actionable_errors_have_local_help_topics_or_docs_urls() -> None:
    for code, policy in POLICIES.items():
        if policy.recommended_action == RecommendedAction.NONE:
            continue
        assert code in HELP_TOPICS, f"{code.value} needs local help or docs mapping"


def test_structured_error_serializes_help_topic_for_local_recovery() -> None:
    error = diagnostic_error(
        code=ErrorCode.AUTH_TOKEN_MISSING,
        category=ErrorCategory.AUTH,
        request_id="req-auth",
        diagnostic={"reason": "authorization missing"},
    )

    serialized = error.model_dump(mode="json")

    assert serialized["help_topic"] == "pairing-token"
    assert serialized["docs_url"] is None
    assert serialized["recommended_action"] == "pair_client"

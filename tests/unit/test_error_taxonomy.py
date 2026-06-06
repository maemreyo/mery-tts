from datetime import UTC, datetime

from mery_tts.errors import (
    ErrorCategory,
    ErrorCode,
    ErrorRecoverability,
    ErrorSeverity,
    FallbackPolicy,
    LocalTTSError,
    RecommendedAction,
)


def test_local_tts_error_shape_is_stable() -> None:
    error = LocalTTSError(
        code=ErrorCode.AUTH_TOKEN_MISSING,
        category=ErrorCategory.AUTH,
        severity=ErrorSeverity.ERROR,
        recoverability=ErrorRecoverability.USER_ACTION,
        user_message_key="errors.auth.token_missing",
        recommended_action=RecommendedAction.PAIR_CLIENT,
        fallback_policy=FallbackPolicy.NONE,
        sanitized_diagnostic="Authorization bearer token is missing.",
        request_id="req_123",
        timestamp=datetime(2026, 6, 5, 12, 0, tzinfo=UTC),
    )

    assert error.model_dump(mode="json") == {
        "code": "auth.token_missing",
        "category": "auth",
        "severity": "error",
        "recoverability": "user_action",
        "user_message_key": "errors.auth.token_missing",
        "recommended_action": "pair_client",
        "fallback_policy": "none",
        "sanitized_diagnostic": "Authorization bearer token is missing.",
        "request_id": "req_123",
        "timestamp": "2026-06-05T12:00:00Z",
    }


def test_error_taxonomy_covers_required_categories() -> None:
    assert {category.value for category in ErrorCategory} == {
        "connection",
        "auth",
        "catalog",
        "model",
        "engine",
        "synthesis",
        "playback",
        "storage",
        "security",
    }


def test_machine_codes_are_stable_typed_values() -> None:
    assert {code.value for code in ErrorCode} >= {
        "connection.daemon_unreachable",
        "auth.token_missing",
        "catalog.signature_invalid",
        "model.install_failed",
        "engine.unavailable",
        "synthesis.failed",
        "playback.device_unavailable",
        "storage.manifest_missing",
        "security.unsafe_identifier",
    }


def test_all_error_codes_follow_category_dot_specific_naming_convention() -> None:
    categories = {category.value for category in ErrorCategory}

    for code in ErrorCode:
        parts = code.value.split(".")
        assert len(parts) == 2, f"Error code {code.value} must be category.specific"
        category, specific = parts
        assert category in categories, f"Error code {code.value} has unknown category"
        assert specific, f"Error code {code.value} has empty specific part"
        assert "_" in specific or specific.isalpha(), (
            f"Error code {code.value} has invalid specific part"
        )


def test_all_error_codes_have_consistent_user_message_key_pattern() -> None:
    for code in ErrorCode:
        assert code.value.count(".") == 1, f"Error code {code.value} must have exactly one dot"
        category, specific = code.value.split(".")
        assert category.isalpha(), f"Error code {code.value} category must be alphabetic"
        assert "_" in specific or specific.isalpha(), (
            f"Error code {code.value} specific part must use underscores or be alphabetic"
        )

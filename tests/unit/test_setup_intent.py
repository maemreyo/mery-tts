"""Tests for setup intent contract (ADR-0026)."""

from __future__ import annotations

from mery_tts.setup.intent import (
    KNOWN_CLIENTS,
    KNOWN_INTENTS,
    SetupIntent,
    SetupIntentError,
    validate_setup_intent,
)


def test_valid_zam_reader_intent() -> None:
    result = validate_setup_intent(client="zam-reader", intent="english-reading")
    assert result.is_valid
    assert result.intent is not None
    assert result.intent.client == "zam-reader"
    assert result.intent.intent == "english-reading"


def test_valid_generic_client() -> None:
    result = validate_setup_intent(client="generic", intent="general")
    assert result.is_valid
    assert result.intent is not None
    assert result.intent.client == "generic"


def test_valid_with_locale() -> None:
    result = validate_setup_intent(client="zam-reader", intent="english-reading", locale="en-US")
    assert result.is_valid
    assert result.intent is not None
    assert result.intent.locale == "en-US"


def test_valid_with_return_url() -> None:
    result = validate_setup_intent(
        client="zam-reader",
        intent="english-reading",
        return_url="http://127.0.0.1:3000/callback",
    )
    assert result.is_valid
    assert result.intent is not None
    assert result.intent.return_url == "http://127.0.0.1:3000/callback"


def test_missing_client() -> None:
    result = validate_setup_intent(client=None, intent="english-reading")
    assert not result.is_valid
    assert result.error == SetupIntentError.MISSING_CLIENT


def test_empty_client() -> None:
    result = validate_setup_intent(client="", intent="english-reading")
    assert not result.is_valid
    assert result.error == SetupIntentError.MISSING_CLIENT


def test_missing_intent() -> None:
    result = validate_setup_intent(client="zam-reader", intent=None)
    assert not result.is_valid
    assert result.error == SetupIntentError.MISSING_INTENT


def test_empty_intent() -> None:
    result = validate_setup_intent(client="zam-reader", intent="")
    assert not result.is_valid
    assert result.error == SetupIntentError.MISSING_INTENT


def test_unknown_client_strict() -> None:
    result = validate_setup_intent(
        client="unknown-client", intent="english-reading", strict_clients=True
    )
    assert not result.is_valid
    assert result.error == SetupIntentError.UNKNOWN_CLIENT


def test_unknown_client_non_strict_accepted() -> None:
    result = validate_setup_intent(
        client="future-browser-ext", intent="english-reading", strict_clients=False
    )
    assert result.is_valid
    assert result.intent is not None
    assert result.intent.client == "future-browser-ext"


def test_unknown_intent_strict() -> None:
    result = validate_setup_intent(
        client="zam-reader", intent="klingon-reading", strict_intents=True
    )
    assert not result.is_valid
    assert result.error == SetupIntentError.UNKNOWN_INTENT


def test_unknown_intent_non_strict_accepted() -> None:
    result = validate_setup_intent(
        client="zam-reader", intent="klingon-reading", strict_intents=False
    )
    assert result.is_valid


def test_unsafe_client_url_rejected() -> None:
    result = validate_setup_intent(client="http://evil.com", intent="english-reading")
    assert not result.is_valid
    assert result.error == SetupIntentError.UNSAFE_PARAMETER


def test_unsafe_client_path_rejected() -> None:
    result = validate_setup_intent(client="../../../etc/passwd", intent="english-reading")
    assert not result.is_valid
    assert result.error == SetupIntentError.UNSAFE_PARAMETER


def test_unsafe_intent_path_rejected() -> None:
    result = validate_setup_intent(client="zam-reader", intent="~/secrets")
    assert not result.is_valid
    assert result.error == SetupIntentError.UNSAFE_PARAMETER


def test_unsafe_return_url_rejected() -> None:
    result = validate_setup_intent(
        client="zam-reader",
        intent="english-reading",
        return_url="http://evil.com/steal",
    )
    assert not result.is_valid
    assert result.error == SetupIntentError.UNSAFE_PARAMETER


def test_return_url_with_credentials_rejected() -> None:
    result = validate_setup_intent(
        client="zam-reader",
        intent="english-reading",
        return_url="http://user:pass@127.0.0.1:3000/callback",
    )
    assert not result.is_valid
    assert result.error == SetupIntentError.UNSAFE_PARAMETER


def test_setup_intent_to_query_params() -> None:
    intent = SetupIntent(
        client="zam-reader",
        intent="english-reading",
        locale="en-US",
    )
    params = intent.to_query_params()
    assert params["client"] == "zam-reader"
    assert params["intent"] == "english-reading"
    assert params["locale"] == "en-US"
    assert "return_url" not in params


def test_setup_intent_to_console_url() -> None:
    intent = SetupIntent(client="zam-reader", intent="english-reading")
    url = intent.to_console_url()
    assert url.startswith("http://127.0.0.1:8765/console/setup?")
    assert "client=zam-reader" in url
    assert "intent=english-reading" in url


def test_setup_intent_to_safe_dict() -> None:
    intent = SetupIntent(
        client="zam-reader",
        intent="english-reading",
        locale="en-US",
    )
    safe = intent.to_safe_dict()
    assert safe["client"] == "zam-reader"
    assert safe["intent"] == "english-reading"
    assert safe["locale"] == "en-US"
    assert "return_url" not in safe


def test_no_install_action_from_parsing() -> None:
    """Parsing intent alone must not trigger any install action."""
    result = validate_setup_intent(client="zam-reader", intent="english-reading")
    assert result.is_valid
    # No side effects — intent is pure data


def test_known_clients_includes_zam_reader() -> None:
    assert "zam-reader" in KNOWN_CLIENTS


def test_known_intents_includes_english_reading() -> None:
    assert "english-reading" in KNOWN_INTENTS


def test_client_case_normalized() -> None:
    result = validate_setup_intent(client="Zam-Reader", intent="English-Reading")
    assert result.is_valid
    assert result.intent is not None
    assert result.intent.client == "zam-reader"
    assert result.intent.intent == "english-reading"

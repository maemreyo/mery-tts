import pytest

from mery_tts.security.guards import reject_unsafe_identifier, security_event_metadata


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "   ",
        "../secret",
        "a/b",
        "a\\b",
        "/tmp/model.onnx",
        "C:\\model.onnx",
        "http://example.com/model.onnx",
        "https://example.com/model.onnx",
        "file:///tmp/model.onnx",
        "~/model.onnx",
        "~model",
    ],
)
def test_reject_unsafe_identifier_before_domain_work(bad: str) -> None:
    with pytest.raises(ValueError):
        reject_unsafe_identifier(bad)


def test_safe_identifier_is_returned() -> None:
    assert reject_unsafe_identifier("piper-plus.vi-vn.demo") == "piper-plus.vi-vn.demo"


def test_security_event_metadata_sanitizes_auth_rate_limit_and_path_rejection() -> None:
    metadata = security_event_metadata(
        event="auth_failure",
        diagnostic={
            "token": "secret",
            "raw_text": "private",
            "page_url": "https://example.com",
            "model_id": "../secret",
            "reason": "invalid token",
        },
    )

    assert metadata == {"event": "auth_failure", "reason": "invalid token"}


def test_security_event_metadata_falls_back_for_unsafe_event_name() -> None:
    metadata = security_event_metadata(
        event="bearer secret from /Users/me",
        diagnostic={"reason": "invalid token"},
    )

    assert metadata == {"event": "security_event", "reason": "invalid token"}


def test_request_too_large_response_preserves_limit_in_sanitized_diagnostic() -> None:
    from mery_tts.api.app import _request_too_large_response

    response = _request_too_large_response(limit=1_000_000)
    payload = bytes(response.body).decode("utf-8")

    assert response.status_code == 413
    assert "security.request_too_large" in payload
    assert "limit=1000000" in payload


def test_request_too_large_response_honors_custom_status_code() -> None:
    from mery_tts.api.app import _request_too_large_response

    response = _request_too_large_response(limit=512, status_code=400)

    assert response.status_code == 400
    assert "limit=512" in bytes(response.body).decode("utf-8")

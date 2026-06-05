import pytest

from mery_tts.security.guards import reject_unsafe_identifier, security_event_metadata


@pytest.mark.parametrize("bad", ["../secret", "a/b", "a\\b", "/tmp/model.onnx", "C:\\model.onnx"])
def test_reject_unsafe_model_identifier_before_domain_work(bad: str) -> None:
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

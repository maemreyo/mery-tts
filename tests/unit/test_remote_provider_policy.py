from mery_tts.audit import AuditEventType
from mery_tts.remote_policy import (
    RemoteProviderPolicy,
    RemoteProviderPolicyError,
    remote_provider_audit_metadata,
)


def test_remote_provider_policy_is_disabled_by_default() -> None:
    policy = RemoteProviderPolicy()

    assert policy.enabled_providers == {}
    assert policy.is_enabled("openai") is False
    assert policy.fallback_allowed("openai") is False

    try:
        policy.require_enabled("openai", operation="synthesis")
    except RemoteProviderPolicyError as exc:
        assert exc.code == "remote_provider.disabled"
        assert exc.provider_id == "openai"
        assert exc.operation == "synthesis"
        assert exc.to_diagnostic() == {
            "reason": "remote_provider_disabled",
            "provider_id": "openai",
            "operation": "synthesis",
        }
    else:
        raise AssertionError("disabled remote provider should require explicit opt-in")


def test_remote_provider_policy_requires_explicit_fallback_opt_in() -> None:
    policy = RemoteProviderPolicy(
        enabled_providers={"openai": True},
        fallback_providers={},
    )

    assert policy.is_enabled("openai") is True
    assert policy.fallback_allowed("openai") is False

    try:
        policy.require_fallback_allowed("openai")
    except RemoteProviderPolicyError as exc:
        assert exc.code == "remote_provider.fallback_disabled"
        assert exc.to_diagnostic() == {
            "reason": "remote_provider_fallback_disabled",
            "provider_id": "openai",
            "operation": "fallback",
        }
    else:
        raise AssertionError("remote provider fallback should need explicit opt-in")


def test_remote_provider_policy_allows_explicit_provider_and_sanitizes_audit_metadata() -> None:
    policy = RemoteProviderPolicy(
        enabled_providers={"openai": True},
        fallback_providers={"openai": True},
    )

    policy.require_enabled("openai", operation="synthesis")
    policy.require_fallback_allowed("openai")

    metadata = remote_provider_audit_metadata(
        provider_id="openai",
        operation="synthesis",
        fallback_used=True,
        client_id="zam-reader",
        request_metadata={
            "text_length": 42,
            "locale": "en-US",
            "raw_text": "private prompt",
            "token": "secret-token",
            "private_path": "/Users/me/private.wav",
        },
    )

    assert metadata["event_type"] == AuditEventType.SECURITY_CONFIG_CHANGED
    assert metadata["metadata"] == {
        "provider_id": "openai",
        "operation": "synthesis",
        "fallback_used": True,
        "client_id": "zam-reader",
        "text_length": 42,
        "locale": "en-US",
    }
    serialized = str(metadata)
    assert "private prompt" not in serialized
    assert "secret-token" not in serialized
    assert "/Users/me" not in serialized

from datetime import UTC, datetime, timedelta

from mery_tts.audit import AuditEventType
from mery_tts.direct_install import (
    DirectInstallGrant,
    DirectInstallGrantDecision,
    DirectInstallGrantPolicy,
    direct_install_audit_metadata,
)


def test_direct_install_policy_is_disabled_by_default() -> None:
    policy = DirectInstallGrantPolicy()

    decision = policy.evaluate(
        client_id="zam-reader",
        install_class="voice-pack",
        now=datetime(2026, 6, 11, tzinfo=UTC),
    )

    assert decision == DirectInstallGrantDecision(
        allowed=False,
        reason="direct_install.disabled",
        grant_id=None,
    )


def test_direct_install_grants_are_scoped_expiring_and_revocable() -> None:
    now = datetime(2026, 6, 11, tzinfo=UTC)
    grant = DirectInstallGrant(
        grant_id="grant-1",
        client_id="zam-reader",
        allowed_install_classes=("voice-pack",),
        expires_at=now + timedelta(minutes=5),
        user_confirmed=True,
    )
    policy = DirectInstallGrantPolicy(enabled=True, grants=(grant,))

    assert policy.evaluate(
        client_id="zam-reader",
        install_class="voice-pack",
        now=now,
    ) == DirectInstallGrantDecision(
        allowed=True,
        reason="direct_install.allowed",
        grant_id="grant-1",
    )
    assert policy.evaluate(
        client_id="other-client",
        install_class="voice-pack",
        now=now,
    ).reason == "direct_install.client_mismatch"
    assert policy.evaluate(
        client_id="zam-reader",
        install_class="provider-runtime",
        now=now,
    ).reason == "direct_install.install_class_denied"
    assert policy.evaluate(
        client_id="zam-reader",
        install_class="voice-pack",
        now=now + timedelta(minutes=6),
    ).reason == "direct_install.expired"
    revoked = grant.model_copy(update={"revoked": True})
    assert DirectInstallGrantPolicy(enabled=True, grants=(revoked,)).evaluate(
        client_id="zam-reader",
        install_class="voice-pack",
        now=now,
    ).reason == "direct_install.revoked"


def test_direct_install_requires_user_confirmation_and_local_policy() -> None:
    now = datetime(2026, 6, 11, tzinfo=UTC)
    unconfirmed = DirectInstallGrant(
        grant_id="grant-2",
        client_id="zam-reader",
        allowed_install_classes=("voice-pack",),
        expires_at=now + timedelta(minutes=5),
        user_confirmed=False,
    )

    assert DirectInstallGrantPolicy(enabled=True, grants=(unconfirmed,)).evaluate(
        client_id="zam-reader",
        install_class="voice-pack",
        now=now,
    ).reason == "direct_install.user_confirmation_required"
    assert DirectInstallGrantPolicy(
        enabled=True,
        grants=(unconfirmed.model_copy(update={"user_confirmed": True}),),
        local_only=True,
    ).evaluate(
        client_id="zam-reader",
        install_class="voice-pack",
        now=now,
    ).reason == "network_disabled:local_only:direct_install"
    assert DirectInstallGrantPolicy(
        enabled=True,
        grants=(unconfirmed.model_copy(update={"user_confirmed": True}),),
        air_gapped=True,
    ).evaluate(
        client_id="zam-reader",
        install_class="voice-pack",
        now=now,
    ).reason == "network_disabled:air_gapped:direct_install"


def test_direct_install_grant_audit_metadata_is_sanitized() -> None:
    metadata = direct_install_audit_metadata(
        grant_id="grant-1",
        client_id="zam-reader",
        install_class="voice-pack",
        outcome="success",
        request_metadata={
            "model_id": "pack.en-us",
            "raw_text": "private text",
            "token": "secret-token",
            "private_path": "/Users/me/private/model.onnx",
        },
    )

    assert metadata["event_type"] == AuditEventType.DIRECT_INSTALL_GRANT_CREATED
    assert metadata["metadata"] == {
        "grant_id": "grant-1",
        "client_id": "zam-reader",
        "install_class": "voice-pack",
        "outcome": "success",
        "model_id": "pack.en-us",
    }
    serialized = str(metadata)
    assert "private text" not in serialized
    assert "secret-token" not in serialized
    assert "/Users/me" not in serialized

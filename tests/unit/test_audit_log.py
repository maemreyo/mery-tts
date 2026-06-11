from datetime import UTC, datetime, timedelta

from mery_tts.audit import AuditEvent, AuditEventStore, AuditEventType
from mery_tts.diagnostics.history import DiagnosticsEventStore


def test_audit_event_schema_sanitizes_security_sensitive_metadata() -> None:
    event = AuditEvent(
        event_id="audit-1",
        event_type=AuditEventType.PAIRING_CLAIMED,
        occurred_at=datetime(2026, 6, 11, tzinfo=UTC),
        actor="console-client",
        action="pairing.claimed",
        outcome="success",
        metadata={
            "client_id": "zam-reader",
            "raw_text": "read this private paragraph",
            "token": "secret-token",
            "reference_audio": b"audio-bytes",
            "private_path": "/Users/me/private/model.onnx",
        },
    )

    payload = event.to_dict()

    assert payload == {
        "schemaVersion": "v1",
        "eventId": "audit-1",
        "eventType": "pairing.claimed",
        "occurredAt": "2026-06-11T00:00:00+00:00",
        "actor": "console-client",
        "action": "pairing.claimed",
        "outcome": "success",
        "metadata": {"client_id": "zam-reader"},
    }
    serialized = str(payload)
    assert "private paragraph" not in serialized
    assert "secret-token" not in serialized
    assert "audio-bytes" not in serialized
    assert "/Users/me" not in serialized


def test_audit_store_is_bounded_and_separate_from_diagnostics(tmp_path) -> None:
    store = AuditEventStore(data_dir=tmp_path, retention_days=7, max_events=2)
    diagnostics = DiagnosticsEventStore(data_dir=tmp_path)
    now = datetime(2026, 6, 11, tzinfo=UTC)

    store.append(
        AuditEvent(
            event_id="old",
            event_type=AuditEventType.AUTH_CREDENTIAL_ROTATED,
            occurred_at=now - timedelta(days=9),
            actor="cli",
            action="token.rotated",
            outcome="success",
            metadata={},
        ),
        now=now,
    )
    for index in range(3):
        store.append(
            AuditEvent(
                event_id=f"evt-{index}",
                event_type=AuditEventType.INSTALL_CONFIRMED,
                occurred_at=now + timedelta(minutes=index),
                actor="console-client",
                action="install.confirmed",
                outcome="success",
                metadata={"model_id": f"voice-{index}"},
            ),
            now=now + timedelta(minutes=index),
        )

    retained = store.load_all(now=now + timedelta(minutes=3))

    assert [event.event_id for event in retained] == ["evt-1", "evt-2"]
    assert (tmp_path / "audit" / "events.json").exists()
    assert not (tmp_path / "diagnostics" / "events.json").exists()
    assert diagnostics.load_all(now=now) == []


def test_audit_event_types_cover_security_boundaries() -> None:
    assert AuditEventType.PAIRING_CREATED == "pairing.created"
    assert AuditEventType.PAIRING_CLAIMED == "pairing.claimed"
    assert AuditEventType.AUTH_CREDENTIAL_ROTATED == "token.rotated"
    assert AuditEventType.INSTALL_CONFIRMED == "install.confirmed"
    assert AuditEventType.DIRECT_INSTALL_GRANT_CREATED == "direct_install_grant.created"
    assert AuditEventType.CATALOG_SOURCE_CHANGED == "catalog.source_changed"
    assert AuditEventType.SECURITY_CONFIG_CHANGED == "security_config.changed"

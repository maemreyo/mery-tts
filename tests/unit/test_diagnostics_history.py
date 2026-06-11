from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from mery_tts.diagnostics.history import (
    DiagnosticsEvent,
    DiagnosticsEventStore,
    DiagnosticsEventType,
)


def _event(
    event_type: DiagnosticsEventType,
    *,
    occurred_at: datetime,
    sequence: int,
    metadata: dict[str, object] | None = None,
) -> DiagnosticsEvent:
    return DiagnosticsEvent(
        event_id=f"evt-{sequence}",
        event_type=event_type,
        occurred_at=occurred_at,
        severity="info",
        source="test",
        message=f"event {sequence}",
        metadata=metadata or {},
    )


def test_diagnostics_event_schema_covers_required_event_families(tmp_path: Path) -> None:
    store = DiagnosticsEventStore(data_dir=tmp_path)
    now = datetime(2026, 1, 8, tzinfo=UTC)

    for index, event_type in enumerate(
        [
            "runtime.startup",
            "runtime.shutdown",
            "discovery.completed",
            "provider.health",
            "install.queued",
            "install.completed",
            "readiness.changed",
            "smoke.completed",
            "synthesis.metadata",
            "fallback.used",
            "synthesis.cancelled",
            "error.sanitized",
        ]
    ):
        store.append(_event(event_type, occurred_at=now, sequence=index))

    events = store.load_all(now=now)

    assert [event.event_type for event in events] == [
        "runtime.startup",
        "runtime.shutdown",
        "discovery.completed",
        "provider.health",
        "install.queued",
        "install.completed",
        "readiness.changed",
        "smoke.completed",
        "synthesis.metadata",
        "fallback.used",
        "synthesis.cancelled",
        "error.sanitized",
    ]
    assert events[0].schema_version == "v1"
    assert events[0].metadata == {}


def test_diagnostics_history_retains_newest_1000_events(tmp_path: Path) -> None:
    store = DiagnosticsEventStore(data_dir=tmp_path)
    now = datetime(2026, 1, 8, tzinfo=UTC)

    for index in range(1005):
        store.append(_event("synthesis.metadata", occurred_at=now, sequence=index))

    events = store.load_all(now=now)

    assert len(events) == 1000
    assert events[0].event_id == "evt-5"
    assert events[-1].event_id == "evt-1004"


def test_diagnostics_history_retains_only_last_7_days(tmp_path: Path) -> None:
    store = DiagnosticsEventStore(data_dir=tmp_path)
    now = datetime(2026, 1, 8, tzinfo=UTC)

    store.append(_event("runtime.startup", occurred_at=now - timedelta(days=8), sequence=1))
    store.append(_event("runtime.startup", occurred_at=now - timedelta(days=7), sequence=2))
    store.append(_event("runtime.startup", occurred_at=now - timedelta(days=1), sequence=3))

    events = store.load_all(now=now)

    assert [event.event_id for event in events] == ["evt-2", "evt-3"]


def test_corrupt_diagnostics_history_storage_loads_empty_and_recovers(tmp_path: Path) -> None:
    store_path = tmp_path / "diagnostics" / "events.json"
    store_path.parent.mkdir(parents=True)
    store_path.write_text("{not-json")
    store = DiagnosticsEventStore(data_dir=tmp_path)
    now = datetime(2026, 1, 8, tzinfo=UTC)

    assert store.load_all(now=now) == []

    store.append(_event("runtime.startup", occurred_at=now, sequence=1))

    assert [event.event_id for event in store.load_all(now=now)] == ["evt-1"]
    payload = json.loads(store_path.read_text())
    assert payload["events"][0]["eventId"] == "evt-1"


def test_diagnostics_history_retention_status_and_clear(tmp_path: Path) -> None:
    store = DiagnosticsEventStore(data_dir=tmp_path)
    now = datetime(2026, 1, 8, tzinfo=UTC)
    store.append(_event("runtime.startup", occurred_at=now - timedelta(days=1), sequence=1))
    store.append(_event("synthesis.metadata", occurred_at=now, sequence=2))

    status = store.retention_status(now=now)

    assert status == {
        "event_count": 2,
        "retention_days": 7,
        "max_events": 1000,
        "oldest_event_at": (now - timedelta(days=1)).isoformat(),
        "newest_event_at": now.isoformat(),
        "storage_corrupted": False,
    }

    assert store.clear() == 2
    assert store.load_all(now=now) == []
    assert store.retention_status(now=now)["event_count"] == 0


def test_diagnostics_history_retention_status_reports_corrupt_storage(tmp_path: Path) -> None:
    store_path = tmp_path / "diagnostics" / "events.json"
    store_path.parent.mkdir(parents=True)
    store_path.write_text("{not-json")

    status = DiagnosticsEventStore(data_dir=tmp_path).retention_status(
        now=datetime(2026, 1, 8, tzinfo=UTC)
    )

    assert status["event_count"] == 0
    assert status["storage_corrupted"] is True


def test_diagnostics_history_redacts_sensitive_metadata_matrix(tmp_path: Path) -> None:
    store = DiagnosticsEventStore(data_dir=tmp_path)
    now = datetime(2026, 1, 8, tzinfo=UTC)

    store.append(
        _event(
            "error.sanitized",
            occurred_at=now,
            sequence=1,
            metadata={
                "raw_text": "hello secret user text",
                "text": "do not keep me",
                "token": "Bearer secret-token",
                "api_key": "sk-secret",
                "audio": b"RIFF....",
                "audio_b64": "UklGRg==",
                "path": "/Users/private/model.onnx",
                "private_path": "/home/me/.mery/private",
                "trace": "Traceback (most recent call last)",
                "voice_id": "voice.en.demo",
                "duration_ms": 123,
                "fallback_used": True,
            },
        )
    )

    metadata = store.load_all(now=now)[0].metadata

    assert metadata == {
        "voice_id": "voice.en.demo",
        "duration_ms": 123,
        "fallback_used": True,
    }

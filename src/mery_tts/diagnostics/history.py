from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, TypedDict

from mery_tts.errors import sanitize_diagnostic

DEFAULT_RETENTION_DAYS = 7
DEFAULT_MAX_EVENTS = 1000

DiagnosticsSeverity = Literal["info", "warning", "error"]


class DiagnosticsRetentionStatus(TypedDict):
    event_count: int
    retention_days: int
    max_events: int
    oldest_event_at: str | None
    newest_event_at: str | None
    storage_corrupted: bool


class DiagnosticsEventType(StrEnum):
    RUNTIME_STARTUP = "runtime.startup"
    RUNTIME_SHUTDOWN = "runtime.shutdown"
    DISCOVERY_STARTED = "discovery.started"
    DISCOVERY_COMPLETED = "discovery.completed"
    PROVIDER_HEALTH = "provider.health"
    INSTALL_QUEUED = "install.queued"
    INSTALL_STARTED = "install.started"
    INSTALL_PROGRESS = "install.progress"
    INSTALL_COMPLETED = "install.completed"
    INSTALL_FAILED = "install.failed"
    READINESS_CHANGED = "readiness.changed"
    SMOKE_STARTED = "smoke.started"
    SMOKE_COMPLETED = "smoke.completed"
    SYNTHESIS_METADATA = "synthesis.metadata"
    FALLBACK_USED = "fallback.used"
    SYNTHESIS_CANCELLED = "synthesis.cancelled"
    ERROR_SANITIZED = "error.sanitized"


@dataclass(frozen=True, slots=True)
class DiagnosticsEvent:
    event_id: str
    event_type: DiagnosticsEventType | str
    occurred_at: datetime
    severity: DiagnosticsSeverity
    source: str
    message: str
    metadata: dict[str, Any]
    schema_version: Literal["v1"] = "v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "eventId": self.event_id,
            "eventType": str(self.event_type),
            "occurredAt": self.occurred_at.isoformat(),
            "severity": self.severity,
            "source": self.source,
            "message": self.message,
            "metadata": sanitize_diagnostics_metadata(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DiagnosticsEvent:
        return cls(
            event_id=str(data["eventId"]),
            event_type=str(data["eventType"]),
            occurred_at=datetime.fromisoformat(str(data["occurredAt"])),
            severity=_severity(str(data.get("severity", "info"))),
            source=str(data.get("source", "runtime")),
            message=str(data.get("message", "diagnostic event")),
            metadata=sanitize_diagnostics_metadata(_metadata(data.get("metadata"))),
        )


def sanitize_diagnostics_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
    without_binary = {
        key: value
        for key, value in metadata.items()
        if not _is_forbidden_diagnostics_key(key) and not isinstance(value, bytes | bytearray)
    }
    return sanitize_diagnostic(without_binary)


def _is_forbidden_diagnostics_key(key: str) -> bool:
    normalized = key.lower()
    return normalized in {
        "audio",
        "audio_b64",
        "audio_base64",
        "audio_bytes",
        "private_path",
        "path",
    }


def _metadata(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return {}


def _severity(value: str) -> DiagnosticsSeverity:
    if value in {"info", "warning", "error"}:
        return value
    return "info"


class DiagnosticsEventStore:
    def __init__(
        self,
        *,
        data_dir: Path,
        retention_days: int = DEFAULT_RETENTION_DAYS,
        max_events: int = DEFAULT_MAX_EVENTS,
    ) -> None:
        self._store_path = data_dir / "diagnostics" / "events.json"
        self._retention_days = retention_days
        self._max_events = max_events

    def load_all(self, *, now: datetime | None = None) -> list[DiagnosticsEvent]:
        events, _corrupted = self._load_unbounded_with_status()
        return self._apply_retention(events, now=now or datetime.now(UTC))

    def append(self, event: DiagnosticsEvent, *, now: datetime | None = None) -> None:
        events, _corrupted = self._load_unbounded_with_status()
        events.append(event)
        retained = self._apply_retention(events, now=now or event.occurred_at)
        self._write_all(retained)

    def retention_status(self, *, now: datetime | None = None) -> DiagnosticsRetentionStatus:
        events, corrupted = self._load_unbounded_with_status()
        retained = self._apply_retention(events, now=now or datetime.now(UTC))
        return {
            "event_count": len(retained),
            "retention_days": self._retention_days,
            "max_events": self._max_events,
            "oldest_event_at": retained[0].occurred_at.isoformat() if retained else None,
            "newest_event_at": retained[-1].occurred_at.isoformat() if retained else None,
            "storage_corrupted": corrupted,
        }

    def clear(self) -> int:
        events, _corrupted = self._load_unbounded_with_status()
        deleted = len(events)
        self._write_all([])
        return deleted

    def _load_unbounded_with_status(self) -> tuple[list[DiagnosticsEvent], bool]:
        if not self._store_path.exists():
            return [], False
        try:
            data = json.loads(self._store_path.read_text())
            return [DiagnosticsEvent.from_dict(entry) for entry in data.get("events", [])], False
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, OSError):
            return [], True

    def _apply_retention(
        self,
        events: list[DiagnosticsEvent],
        *,
        now: datetime,
    ) -> list[DiagnosticsEvent]:
        cutoff = now - timedelta(days=self._retention_days)
        retained = [event for event in events if event.occurred_at >= cutoff]
        return retained[-self._max_events :]

    def _write_all(self, events: list[DiagnosticsEvent]) -> None:
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "updatedAt": datetime.now(UTC).isoformat(),
            "retentionDays": self._retention_days,
            "maxEvents": self._max_events,
            "events": [event.to_dict() for event in events],
        }
        temp_path = self._store_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        temp_path.replace(self._store_path)


__all__ = [
    "DEFAULT_MAX_EVENTS",
    "DEFAULT_RETENTION_DAYS",
    "DiagnosticsEvent",
    "DiagnosticsEventStore",
    "DiagnosticsEventType",
    "DiagnosticsRetentionStatus",
    "sanitize_diagnostics_metadata",
]

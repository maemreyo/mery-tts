from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, cast

from mery_tts.errors import sanitize_diagnostic

DEFAULT_AUDIT_RETENTION_DAYS = 30
DEFAULT_AUDIT_MAX_EVENTS = 2000

AuditOutcome = Literal["success", "denied", "failed"]


class AuditEventType(StrEnum):
    PAIRING_CREATED = "pairing.created"
    PAIRING_CLAIMED = "pairing.claimed"
    AUTH_CREDENTIAL_ROTATED = "token.rotated"
    INSTALL_CONFIRMED = "install.confirmed"
    DIRECT_INSTALL_GRANT_CREATED = "direct_install_grant.created"
    CATALOG_SOURCE_CHANGED = "catalog.source_changed"
    SECURITY_CONFIG_CHANGED = "security_config.changed"


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    event_type: AuditEventType | str
    occurred_at: datetime
    actor: str
    action: str
    outcome: AuditOutcome
    metadata: dict[str, Any]
    schema_version: Literal["v1"] = "v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "eventId": self.event_id,
            "eventType": str(self.event_type),
            "occurredAt": self.occurred_at.isoformat(),
            "actor": str(sanitize_diagnostic({"actor": self.actor}).get("actor", "unknown")),
            "action": self.action,
            "outcome": self.outcome,
            "metadata": sanitize_audit_metadata(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditEvent:
        return cls(
            event_id=str(data["eventId"]),
            event_type=str(data["eventType"]),
            occurred_at=datetime.fromisoformat(str(data["occurredAt"])),
            actor=str(data.get("actor", "unknown")),
            action=str(data.get("action", data.get("eventType", "audit.event"))),
            outcome=_outcome(str(data.get("outcome", "success"))),
            metadata=sanitize_audit_metadata(_metadata(data.get("metadata"))),
        )


def sanitize_audit_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
    allowed = {
        key: value
        for key, value in metadata.items()
        if not _is_forbidden_audit_key(key) and not isinstance(value, bytes | bytearray)
    }
    return sanitize_diagnostic(allowed)


def _is_forbidden_audit_key(key: str) -> bool:
    normalized = key.lower()
    return normalized in {
        "audio",
        "audio_b64",
        "audio_base64",
        "audio_bytes",
        "private_path",
        "path",
        "raw_text",
        "input",
        "text",
        "token",
        "auth_token",
        "authorization",
        "reference_audio",
        "reference_audio_b64",
        "reference_audio_base64",
    }


def _metadata(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return {}


def _outcome(value: str) -> AuditOutcome:
    if value in {"success", "denied", "failed"}:
        return cast("AuditOutcome", value)
    return "failed"


class AuditEventStore:
    def __init__(
        self,
        *,
        data_dir: Path,
        retention_days: int = DEFAULT_AUDIT_RETENTION_DAYS,
        max_events: int = DEFAULT_AUDIT_MAX_EVENTS,
    ) -> None:
        self._store_path = data_dir / "audit" / "events.json"
        self._retention_days = retention_days
        self._max_events = max_events

    def load_all(self, *, now: datetime | None = None) -> list[AuditEvent]:
        events = self._load_unbounded()
        return self._apply_retention(events, now=now or datetime.now(UTC))

    def append(self, event: AuditEvent, *, now: datetime | None = None) -> None:
        events = self._load_unbounded()
        events.append(event)
        retained = self._apply_retention(events, now=now or event.occurred_at)
        self._write_all(retained)

    def _load_unbounded(self) -> list[AuditEvent]:
        if not self._store_path.exists():
            return []
        try:
            data = json.loads(self._store_path.read_text())
            return [AuditEvent.from_dict(entry) for entry in data.get("events", [])]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, OSError):
            return []

    def _apply_retention(self, events: list[AuditEvent], *, now: datetime) -> list[AuditEvent]:
        cutoff = now - timedelta(days=self._retention_days)
        retained = [event for event in events if event.occurred_at >= cutoff]
        return retained[-self._max_events :]

    def _write_all(self, events: list[AuditEvent]) -> None:
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
    "DEFAULT_AUDIT_MAX_EVENTS",
    "DEFAULT_AUDIT_RETENTION_DAYS",
    "AuditEvent",
    "AuditEventStore",
    "AuditEventType",
    "AuditOutcome",
    "sanitize_audit_metadata",
]

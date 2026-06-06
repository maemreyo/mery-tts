"""Per-voice smoke status storage and derivation.

ADR-0025: Smoke status is stored per installed voice and feeds layered health.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class SmokeStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    NOT_RUN = "not_run"


@dataclass(frozen=True, slots=True)
class SmokeRecord:
    """Per-voice smoke test result."""

    voice_id: str
    engine_id: str
    status: SmokeStatus
    checked_at: datetime
    sample_rate_hz: int | None = None
    channels: int | None = None
    duration_ms: int | None = None
    failure_detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "voiceId": self.voice_id,
            "engineId": self.engine_id,
            "status": self.status.value,
            "checkedAt": self.checked_at.isoformat(),
        }
        if self.sample_rate_hz is not None:
            result["sampleRateHz"] = self.sample_rate_hz
        if self.channels is not None:
            result["channels"] = self.channels
        if self.duration_ms is not None:
            result["durationMs"] = self.duration_ms
        if self.failure_detail is not None:
            result["failureDetail"] = _sanitize_failure(self.failure_detail)
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SmokeRecord:
        return cls(
            voice_id=str(data["voiceId"]),
            engine_id=str(data["engineId"]),
            status=SmokeStatus(str(data["status"])),
            checked_at=datetime.fromisoformat(str(data["checkedAt"])),
            sample_rate_hz=data.get("sampleRateHz"),
            channels=data.get("channels"),
            duration_ms=data.get("durationMs"),
            failure_detail=data.get("failureDetail"),
        )


def _sanitize_failure(detail: str) -> str:
    """Sanitize failure details to remove paths, tokens, and sensitive data."""
    sanitized = detail
    for marker in ("Traceback", "traceback", "File ", "/Users/", "/home/"):
        if marker in sanitized:
            sanitized = "diagnostic omitted"
            break
    if len(sanitized) > 200:
        sanitized = sanitized[:200] + "..."
    return sanitized


class SmokeRecordStore:
    """Persists smoke records under Mery-owned app data."""

    def __init__(self, *, data_dir: Path) -> None:
        self._store_path = data_dir / "smoke" / "voice-smoke.json"

    def load_all(self) -> dict[str, SmokeRecord]:
        if not self._store_path.exists():
            return {}
        try:
            data = json.loads(self._store_path.read_text())
            records: dict[str, SmokeRecord] = {}
            for entry in data.get("records", []):
                record = SmokeRecord.from_dict(entry)
                records[record.voice_id] = record
            return records
        except (json.JSONDecodeError, KeyError, ValueError):
            return {}

    def save(self, record: SmokeRecord) -> None:
        existing = self.load_all()
        existing[record.voice_id] = record
        self._write_all(existing)

    def remove(self, voice_id: str) -> None:
        existing = self.load_all()
        existing.pop(voice_id, None)
        self._write_all(existing)

    def get(self, voice_id: str) -> SmokeRecord | None:
        return self.load_all().get(voice_id)

    def _write_all(self, records: dict[str, SmokeRecord]) -> None:
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "updatedAt": datetime.now(UTC).isoformat(),
            "records": [r.to_dict() for r in records.values()],
        }
        temp_path = self._store_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        temp_path.replace(self._store_path)


__all__ = [
    "SmokeRecord",
    "SmokeRecordStore",
    "SmokeStatus",
]

from __future__ import annotations

import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mery_tts import __version__
from mery_tts.catalog import load_bundled_catalog
from mery_tts.diagnostics.history import DiagnosticsEventStore
from mery_tts.errors import sanitize_diagnostic
from mery_tts.smoke.record import SmokeRecordStore


class DiagnosticsExportBuilder:
    def __init__(self, *, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._corrupt_storage_ignored = False

    def build(self) -> dict[str, Any]:
        events = DiagnosticsEventStore(data_dir=self._data_dir).load_all()
        smoke_records = SmokeRecordStore(data_dir=self._data_dir).load_all()
        install_states = self._load_install_states()
        doctor_checks = self._load_doctor_checks()
        catalog = load_bundled_catalog()
        return {
            "schema_version": "v1",
            "bundle_type": "diagnostics_export",
            "generated_at": datetime.now(UTC).isoformat(),
            "versions": {
                "mery_tts": __version__,
                "contract": "v1",
            },
            "platform": {
                "system": platform.system(),
                "machine": platform.machine(),
                "python": platform.python_version(),
            },
            "engine_provider_health": {
                "doctor_checks": doctor_checks,
            },
            "installed_voices": self._installed_voice_summary(),
            "catalog_summary": {
                "voice_count": len(catalog.models),
                "engine_ids": sorted({model.engine_id for model in catalog.models}),
            },
            "install_states": install_states,
            "readiness_smoke": {
                "records": [record.to_dict() for record in smoke_records.values()],
            },
            "recent_diagnostics": [event.to_dict() for event in events],
            "audit_summary": {
                "event_count": len(events),
                "install_state_count": len(install_states),
                "smoke_record_count": len(smoke_records),
                "corrupt_storage_ignored": self._corrupt_storage_ignored,
            },
        }

    def _installed_voice_summary(self) -> dict[str, Any]:
        voices_dir = self._data_dir / "models" / "voices"
        if not voices_dir.exists():
            return {"count": 0, "voices": []}
        voices: list[dict[str, str]] = []
        for manifest_path in sorted(voices_dir.glob("*/manifest.json")):
            try:
                payload = json.loads(manifest_path.read_text())
            except (json.JSONDecodeError, OSError):
                self._corrupt_storage_ignored = True
                continue
            voice_id = str(payload.get("voiceId") or manifest_path.parent.name)
            engine_id = str(payload.get("engineId") or "unknown")
            voices.append({"voice_id": voice_id, "engine_id": engine_id})
        return {"count": len(voices), "voices": voices}

    def _load_install_states(self) -> list[dict[str, Any]]:
        jobs_dir = self._data_dir / "models" / "jobs" / "install"
        if not jobs_dir.exists():
            return []
        states: list[dict[str, Any]] = []
        for job_path in sorted(jobs_dir.glob("*.json")):
            try:
                payload = json.loads(job_path.read_text())
            except (json.JSONDecodeError, OSError):
                self._corrupt_storage_ignored = True
                continue
            sanitized = sanitize_diagnostic(
                {
                    "job_id": payload.get("job_id"),
                    "catalog_entry_id": payload.get("catalog_entry_id"),
                    "voice_id": payload.get("voice_id"),
                    "engine_id": payload.get("engine_id"),
                    "artifact_id": payload.get("artifact_id"),
                    "status": payload.get("status"),
                    "error": payload.get("error"),
                }
            )
            states.append(sanitized)
        return states

    def _load_doctor_checks(self) -> dict[str, str]:
        doctor_path = self._data_dir / "diagnostics" / "last-doctor.json"
        if not doctor_path.exists():
            return {}
        try:
            payload = json.loads(doctor_path.read_text())
        except (json.JSONDecodeError, OSError):
            self._corrupt_storage_ignored = True
            return {}
        checks: dict[str, str] = {}
        for result in payload.get("results", []):
            if not isinstance(result, dict):
                continue
            check = result.get("check")
            status = result.get("status")
            if isinstance(check, str) and isinstance(status, str):
                checks[check] = status
        return checks


__all__ = ["DiagnosticsExportBuilder"]

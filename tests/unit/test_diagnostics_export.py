from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from mery_tts.diagnostics.export import DiagnosticsExportBuilder
from mery_tts.diagnostics.history import DiagnosticsEvent, DiagnosticsEventStore
from mery_tts.smoke.record import SmokeRecord, SmokeRecordStore, SmokeStatus


def test_diagnostics_export_bundle_includes_required_sanitized_sections(tmp_path: Path) -> None:
    DiagnosticsEventStore(data_dir=tmp_path).append(
        DiagnosticsEvent(
            event_id="evt-export-1",
            event_type="error.sanitized",
            occurred_at=datetime.now(UTC),
            severity="error",
            source="test",
            message="sanitized error captured",
            metadata={
                "voice_id": "voice.en.demo",
                "raw_text": "secret text",
                "token": "Bearer secret",
                "api_key": "sk-secret",
                "audio_b64": "UklGRg==",
                "path": "/Users/private/model.onnx",
            },
        )
    )
    SmokeRecordStore(data_dir=tmp_path).save(
        SmokeRecord(
            voice_id="voice.en.demo",
            engine_id="piper-plus",
            status=SmokeStatus.PASSED,
            checked_at=datetime.now(UTC),
            sample_rate_hz=24_000,
            channels=1,
        )
    )

    bundle = DiagnosticsExportBuilder(data_dir=tmp_path).build()

    assert bundle["schema_version"] == "v1"
    assert bundle["bundle_type"] == "diagnostics_export"
    assert "generated_at" in bundle
    assert "versions" in bundle
    assert "platform" in bundle
    assert "engine_provider_health" in bundle
    assert "installed_voices" in bundle
    assert "catalog_summary" in bundle
    assert "install_states" in bundle
    assert "readiness_smoke" in bundle
    assert "recent_diagnostics" in bundle
    assert "audit_summary" in bundle
    assert bundle["readiness_smoke"]["records"][0]["voiceId"] == "voice.en.demo"
    assert bundle["recent_diagnostics"][0]["metadata"] == {"voice_id": "voice.en.demo"}

    serialized = str(bundle)
    assert "secret text" not in serialized
    assert "Bearer secret" not in serialized
    assert "sk-secret" not in serialized
    assert "UklGRg" not in serialized
    assert "/Users/private" not in serialized


def test_diagnostics_export_tolerates_corrupt_history_and_job_storage(tmp_path: Path) -> None:
    diagnostics_dir = tmp_path / "diagnostics"
    diagnostics_dir.mkdir(parents=True)
    (diagnostics_dir / "events.json").write_text("{not-json")
    jobs_dir = tmp_path / "models" / "jobs" / "install"
    jobs_dir.mkdir(parents=True)
    (jobs_dir / "job-bad.json").write_text("{not-json")

    bundle = DiagnosticsExportBuilder(data_dir=tmp_path).build()

    assert bundle["recent_diagnostics"] == []
    assert bundle["install_states"] == []
    assert bundle["audit_summary"]["corrupt_storage_ignored"] is True

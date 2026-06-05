from pathlib import Path

from mery_tts.jobs.install import InstallJobService, JobStatus
from mery_tts.storage.identity import StorageIdentityStore


def test_install_job_commits_voice_manifest_and_refreshes(tmp_path: Path) -> None:
    refreshes: list[str] = []
    service = InstallJobService(
        StorageIdentityStore(tmp_path),
        refresh=lambda: refreshes.append("refresh"),
    )

    job = service.start_install(
        catalog_entry_id="entry.kokoro",
        voice_id="voice.kokoro",
        engine_id="kokoro",
        artifact_id="artifact.kokoro",
    )
    service.complete_install(job.job_id, payload_template={"kind": "preset", "preset_id": "af"})

    assert service.status(job.job_id).status == JobStatus.COMPLETED
    assert refreshes == ["refresh"]
    assert (tmp_path / "voices" / "voice.kokoro.json").exists()


def test_install_failure_before_commit_is_not_routable(tmp_path: Path) -> None:
    service = InstallJobService(StorageIdentityStore(tmp_path), refresh=lambda: None)

    job = service.start_install(
        catalog_entry_id="entry",
        voice_id="voice.fail",
        engine_id="kokoro",
        artifact_id="artifact",
    )
    service.fail_install(job.job_id, reason="download failed")

    assert service.status(job.job_id).status == JobStatus.FAILED
    assert not (tmp_path / "voices" / "voice.fail.json").exists()


def test_delete_is_idempotent_and_garbage_collects(tmp_path: Path) -> None:
    service = InstallJobService(StorageIdentityStore(tmp_path), refresh=lambda: None)
    job = service.start_install(
        catalog_entry_id="entry",
        voice_id="voice.delete",
        engine_id="kokoro",
        artifact_id="artifact.delete",
    )
    service.complete_install(job.job_id, payload_template={"kind": "preset", "preset_id": "af"})

    assert service.delete_voice("voice.delete") == ["artifact.delete"]
    assert service.delete_voice("voice.delete") == []

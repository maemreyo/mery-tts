from pathlib import Path

import pytest

from mery_tts.api.orchestration.install import InstallOrchestrator
from mery_tts.jobs.install import InstallJobService, JobStatus
from mery_tts.models.events import InstallDone, InstallFailed, InstallProgress
from mery_tts.models.manager import ModelInstallManager
from mery_tts.storage.identity import StorageIdentityStore


@pytest.mark.asyncio
async def test_model_install_manager_emits_progress_and_done_without_api_imports(
    tmp_path: Path,
) -> None:
    service = InstallJobService(StorageIdentityStore(tmp_path), refresh=lambda: None)
    manager = ModelInstallManager(service)

    events = [
        event
        async for event in manager.install(
            model_id="kokoro.demo",
            engine_id="kokoro",
            payload_template={"kind": "preset", "preset_id": "af"},
        )
    ]

    assert [type(event) for event in events] == [InstallProgress, InstallProgress, InstallDone]
    assert [
        (event.phase, event.percent) for event in events if isinstance(event, InstallProgress)
    ] == [
        ("queued", 0),
        ("commit", 90),
    ]
    done = events[-1]
    assert isinstance(done, InstallDone)
    assert done.model_id == "kokoro.demo"
    assert done.engine_id == "kokoro"
    assert service.status(done.job_id).status == JobStatus.COMPLETED
    assert (tmp_path / "voices" / "kokoro.demo.json").exists()


@pytest.mark.asyncio
async def test_model_install_manager_emits_failed_when_commit_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service = InstallJobService(StorageIdentityStore(tmp_path), refresh=lambda: None)

    def fail_commit(job_id: str, *, payload_template: dict[str, object]):
        _ = job_id, payload_template
        raise RuntimeError("commit failed")

    monkeypatch.setattr(service, "complete_install", fail_commit)
    manager = ModelInstallManager(service)

    events = [
        event
        async for event in manager.install(
            model_id="kokoro.bad",
            engine_id="kokoro",
            payload_template={"kind": "preset", "preset_id": "af"},
        )
    ]

    assert [type(event) for event in events] == [InstallProgress, InstallProgress, InstallFailed]
    failed = events[-1]
    assert isinstance(failed, InstallFailed)
    assert failed.model_id == "kokoro.bad"
    assert failed.error == "commit failed"
    assert service.status(failed.job_id).status == JobStatus.FAILED
    assert not (tmp_path / "voices" / "kokoro.bad.json").exists()
    assert not (tmp_path / "artifacts" / "kokoro" / "kokoro.bad" / "artifact.json").exists()


@pytest.mark.asyncio
async def test_install_manager_events_refresh_voice_registry_once_after_done(
    tmp_path: Path,
) -> None:
    service = InstallJobService(StorageIdentityStore(tmp_path), refresh=lambda: None)
    manager = ModelInstallManager(service)
    refreshes: list[str] = []

    emitted = await InstallOrchestrator(refresh=lambda: refreshes.append("refresh")).run(
        manager.install(
            model_id="kokoro.refresh",
            engine_id="kokoro",
            payload_template={"kind": "preset", "preset_id": "af"},
        )
    )

    assert [event.event_type for event in emitted] == [
        "install.progress",
        "install.progress",
        "install.completed",
    ]
    assert refreshes == ["refresh"]

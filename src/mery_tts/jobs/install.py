import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol, cast
from uuid import uuid4

from mery_tts.storage.identity import StorageIdentityStore


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class InstallJob:
    job_id: str
    catalog_entry_id: str
    voice_id: str
    engine_id: str
    artifact_id: str
    status: JobStatus
    error: str | None = None


class InstallJobStore(Protocol):
    def save(self, job: InstallJob) -> None: ...

    def load(self, job_id: str) -> InstallJob: ...


class MemoryInstallJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, InstallJob] = {}

    def save(self, job: InstallJob) -> None:
        self._jobs[job.job_id] = job

    def load(self, job_id: str) -> InstallJob:
        return self._jobs[job_id]


class FileInstallJobStore:
    def __init__(self, jobs_dir: Path) -> None:
        self._jobs_dir = jobs_dir

    def save(self, job: InstallJob) -> None:
        self._jobs_dir.mkdir(parents=True, exist_ok=True)
        payload = asdict(job)
        payload["status"] = job.status.value
        path = self._path_for(job.job_id)
        temporary_path = path.with_suffix(".tmp")
        temporary_path.write_text(json.dumps(payload, sort_keys=True))
        temporary_path.replace(path)

    def load(self, job_id: str) -> InstallJob:
        payload = cast("dict[str, object]", json.loads(self._path_for(job_id).read_text()))
        return InstallJob(
            job_id=str(payload["job_id"]),
            catalog_entry_id=str(payload["catalog_entry_id"]),
            voice_id=str(payload["voice_id"]),
            engine_id=str(payload["engine_id"]),
            artifact_id=str(payload["artifact_id"]),
            status=JobStatus(str(payload["status"])),
            error=str(payload["error"]) if payload.get("error") is not None else None,
        )

    def _path_for(self, job_id: str) -> Path:
        return self._jobs_dir / f"{job_id}.json"


class InstallJobService:
    def __init__(
        self,
        store: StorageIdentityStore,
        *,
        refresh: Callable[[], None],
        job_store: InstallJobStore | None = None,
    ) -> None:
        self._store = store
        self._refresh = refresh
        self._job_store = job_store or MemoryInstallJobStore()

    def start_install(
        self,
        *,
        catalog_entry_id: str,
        voice_id: str,
        engine_id: str,
        artifact_id: str,
    ) -> InstallJob:
        job = InstallJob(
            job_id=f"job-{uuid4().hex}",
            catalog_entry_id=catalog_entry_id,
            voice_id=voice_id,
            engine_id=engine_id,
            artifact_id=artifact_id,
            status=JobStatus.RUNNING,
        )
        self._job_store.save(job)
        self._store.write_artifact_manifest(
            engine_id=engine_id,
            artifact_id=artifact_id,
            metadata={"catalogEntryId": catalog_entry_id},
        )
        return job

    def complete_install(self, job_id: str, *, payload_template: dict[str, Any]) -> InstallJob:
        job = self.status(job_id)
        completed = InstallJob(
            job_id=job.job_id,
            catalog_entry_id=job.catalog_entry_id,
            voice_id=job.voice_id,
            engine_id=job.engine_id,
            artifact_id=job.artifact_id,
            status=JobStatus.COMPLETED,
        )
        self._store.write_voice_manifest(
            job.voice_id,
            [job.artifact_id],
            payload_template,
        )
        self._refresh()
        self._job_store.save(completed)
        return completed

    def fail_install(self, job_id: str, *, reason: str) -> InstallJob:
        job = self.status(job_id)
        failed = InstallJob(
            job_id=job.job_id,
            catalog_entry_id=job.catalog_entry_id,
            voice_id=job.voice_id,
            engine_id=job.engine_id,
            artifact_id=job.artifact_id,
            status=JobStatus.FAILED,
            error=reason,
        )
        self._job_store.save(failed)
        self._store.collect_unreferenced_artifacts([job.artifact_id])
        return failed

    def status(self, job_id: str) -> InstallJob:
        return self._job_store.load(job_id)

    def delete_voice(self, voice_id: str) -> list[str]:
        collected = self._store.delete_voice_and_collect_garbage(voice_id)
        self._refresh()
        return collected

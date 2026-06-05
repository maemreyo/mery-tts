from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any
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


class InstallJobService:
    def __init__(self, store: StorageIdentityStore, *, refresh: Callable[[], None]) -> None:
        self._store = store
        self._refresh = refresh
        self._jobs: dict[str, InstallJob] = {}

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
        self._jobs[job.job_id] = job
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
        self._jobs[job_id] = completed
        self._refresh()
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
        self._jobs[job_id] = failed
        return failed

    def status(self, job_id: str) -> InstallJob:
        return self._jobs[job_id]

    def delete_voice(self, voice_id: str) -> list[str]:
        collected = self._store.delete_voice_and_collect_garbage(voice_id)
        self._refresh()
        return collected

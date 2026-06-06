from collections.abc import AsyncIterator
from typing import Any

from mery_tts.jobs.install import InstallJobService
from mery_tts.models.events import InstallDone, InstallEvent, InstallFailed, InstallProgress


class ModelInstallManager:
    def __init__(self, install_jobs: InstallJobService) -> None:
        self._install_jobs = install_jobs

    async def install(
        self,
        *,
        model_id: str,
        engine_id: str,
        voice_id: str | None = None,
        artifact_id: str | None = None,
        payload_template: dict[str, Any] | None = None,
    ) -> AsyncIterator[InstallEvent]:
        target_voice_id = voice_id or model_id
        target_artifact_id = artifact_id or model_id
        job = self._install_jobs.start_install(
            catalog_entry_id=model_id,
            voice_id=target_voice_id,
            engine_id=engine_id,
            artifact_id=target_artifact_id,
        )
        yield InstallProgress(job_id=job.job_id, model_id=model_id, phase="queued", percent=0)
        yield InstallProgress(job_id=job.job_id, model_id=model_id, phase="commit", percent=90)
        try:
            self._install_jobs.complete_install(
                job.job_id,
                payload_template=payload_template or {"kind": "preset", "preset_id": model_id},
            )
        except Exception as exc:
            self._install_jobs.fail_install(job.job_id, reason=str(exc))
            yield InstallFailed(job_id=job.job_id, model_id=model_id, error=str(exc))
            return
        yield InstallDone(job_id=job.job_id, model_id=model_id, engine_id=engine_id)

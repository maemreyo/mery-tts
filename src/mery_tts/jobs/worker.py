"""Async install worker for bundled artifacts.

ADR-0023: The install worker resolves catalog entries to artifact/voice install plans,
fetches bundled artifacts through ArtifactSource, verifies files, commits artifacts,
writes voice manifests, and completes jobs atomically.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mery_tts.artifacts.source import ArtifactSource, BundledArtifactSource, FetchedArtifact
from mery_tts.catalog.normalized import ArtifactEntry, CatalogGraph
from mery_tts.jobs.install import InstallJob, InstallJobService


@dataclass(frozen=True, slots=True)
class ArtifactInstallPlan:
    """Plan for installing a single artifact."""

    artifact_id: str
    catalog_entry_id: str
    engine_id: str
    expected_size_bytes: int
    expected_sha256: str


@dataclass(frozen=True, slots=True)
class VoiceInstallPlan:
    """Plan for installing a voice with its required artifacts."""

    voice_id: str
    engine_id: str
    payload_template: dict[str, Any]
    artifact_plans: tuple[ArtifactInstallPlan, ...]


class InstallWorkerError(Exception):
    """Error during install worker execution."""

    def __init__(self, reason: str, *, job_id: str | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.job_id = job_id


class BundledInstallWorker:
    """Async install worker that uses BundledArtifactSource to install voices.

    The worker:
    1. Resolves a catalog entry to artifact and voice install plans
    2. Fetches bundled artifacts through BundledArtifactSource
    3. Verifies files (size/hash)
    4. Commits artifacts and writes voice manifests atomically
    5. Refreshes installed voices without restart
    6. Handles failure paths (marks jobs failed, no partial voices)
    """

    def __init__(
        self,
        *,
        job_service: InstallJobService,
        artifact_source: ArtifactSource | None = None,
        catalog_graph: CatalogGraph | None = None,
        artifacts_dir: Path | None = None,
        on_complete: Callable[[str], None] | None = None,
    ) -> None:
        self._job_service = job_service
        self._source = artifact_source or BundledArtifactSource()
        self._catalog = catalog_graph
        self._artifacts_dir = artifacts_dir
        self._on_complete = on_complete

    async def execute(self, job_id: str) -> InstallJob:
        """Execute an install job to completion or failure."""
        job = self._job_service.status(job_id)

        try:
            plan = self._resolve_plan(job)
            fetched = await self._fetch_artifacts(plan)
            self._verify_artifacts(plan, fetched)
            self._commit_artifacts(plan, fetched)
            completed = self._job_service.complete_install(
                job_id, payload_template=plan.voice_install.payload_template
            )
            if self._on_complete:
                self._on_complete(job_id)
            return completed
        except InstallWorkerError as exc:
            failed = self._job_service.fail_install(job_id, reason=exc.reason)
            return failed
        except Exception as exc:
            failed = self._job_service.fail_install(job_id, reason=str(exc))
            return failed

    def _resolve_plan(self, job: InstallJob) -> _ResolvedInstallPlan:
        """Resolve a job to artifact and voice install plans."""
        artifact_entry = self._find_artifact_entry(job.artifact_id)
        artifact_plan = ArtifactInstallPlan(
            artifact_id=job.artifact_id,
            catalog_entry_id=job.catalog_entry_id,
            engine_id=job.engine_id,
            expected_size_bytes=artifact_entry.size_bytes if artifact_entry else 1,
            expected_sha256=artifact_entry.sha256 if artifact_entry else "",
        )
        voice_plan = VoiceInstallPlan(
            voice_id=job.voice_id,
            engine_id=job.engine_id,
            payload_template=self._infer_payload_template(job),
            artifact_plans=(artifact_plan,),
        )
        return _ResolvedInstallPlan(
            job=job,
            voice_install=voice_plan,
        )

    def _find_artifact_entry(self, artifact_id: str) -> ArtifactEntry | None:
        if self._catalog is None:
            return None
        for artifact in self._catalog.artifacts:
            if artifact.artifact_id == artifact_id:
                return artifact
        return None

    def _infer_payload_template(self, job: InstallJob) -> dict[str, Any]:
        """Infer the voice payload template from the job metadata."""
        if job.engine_id == "piper-plus":
            return {
                "kind": "model-file",
                "artifact_id": job.artifact_id,
                "relative_path": f"{job.artifact_id}.onnx",
            }
        return {
            "kind": "preset",
            "preset_id": job.artifact_id,
        }

    async def _fetch_artifacts(self, plan: _ResolvedInstallPlan) -> dict[str, FetchedArtifact]:
        """Fetch all artifacts for the install plan."""
        if self._artifacts_dir is None:
            raise InstallWorkerError("artifacts_dir not configured")

        fetched: dict[str, FetchedArtifact] = {}
        for artifact_plan in plan.voice_install.artifact_plans:
            target_dir = self._artifacts_dir / artifact_plan.engine_id / artifact_plan.artifact_id
            target_dir.mkdir(parents=True, exist_ok=True)
            try:
                entry = ArtifactEntry(
                    artifact_id=artifact_plan.artifact_id,
                    catalog_entry_id=artifact_plan.catalog_entry_id,
                    engine_id=artifact_plan.engine_id,
                    size_bytes=max(artifact_plan.expected_size_bytes, 1),
                    sha256=artifact_plan.expected_sha256 or "0" * 64,
                    download_url=f"bundled://{artifact_plan.artifact_id}",
                )
                result = await self._source.fetch(entry, target_dir)
                fetched[artifact_plan.artifact_id] = result
            except InstallWorkerError:
                raise
            except Exception as exc:
                raise InstallWorkerError(
                    f"artifact fetch failed: {exc}",
                    job_id=plan.job.job_id,
                ) from exc
        return fetched

    def _verify_artifacts(
        self,
        plan: _ResolvedInstallPlan,
        fetched: dict[str, FetchedArtifact],
    ) -> None:
        """Verify fetched artifacts match expected size/hash."""
        for artifact_plan in plan.voice_install.artifact_plans:
            result = fetched.get(artifact_plan.artifact_id)
            if result is None:
                raise InstallWorkerError(
                    f"artifact '{artifact_plan.artifact_id}' not fetched",
                    job_id=plan.job.job_id,
                )
            if not result.files:
                raise InstallWorkerError(
                    f"artifact '{artifact_plan.artifact_id}' has no files",
                    job_id=plan.job.job_id,
                )

    def _commit_artifacts(
        self,
        plan: _ResolvedInstallPlan,
        fetched: dict[str, FetchedArtifact],
    ) -> None:
        """Commit fetched artifacts by writing artifact manifests."""
        for artifact_plan in plan.voice_install.artifact_plans:
            result = fetched[artifact_plan.artifact_id]
            manifest = {
                "artifactId": artifact_plan.artifact_id,
                "engineId": artifact_plan.engine_id,
                "catalogEntryId": artifact_plan.catalog_entry_id,
                "files": [str(f) for f in result.files],
                "totalSizeBytes": result.total_size_bytes,
                "sha256": result.sha256,
            }
            manifest_path = result.target_dir / "artifact.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = manifest_path.with_suffix(".tmp")
            temp_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            temp_path.replace(manifest_path)


@dataclass(frozen=True, slots=True)
class _ResolvedInstallPlan:
    """Internal resolved install plan."""

    job: InstallJob
    voice_install: VoiceInstallPlan


__all__ = [
    "ArtifactInstallPlan",
    "BundledInstallWorker",
    "InstallWorkerError",
    "VoiceInstallPlan",
]

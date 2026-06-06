"""Artifact source abstraction for model install.

ADR-0023: ArtifactSource hides whether bytes come from package resources, HTTP, or
a future local import. Only BundledArtifactSource is required for the first milestone.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Protocol, runtime_checkable

from mery_tts.catalog.normalized import ArtifactEntry


class ArtifactFetchError(Exception):
    """Raised when an artifact cannot be fetched from its source."""


@dataclass(frozen=True, slots=True)
class FetchedArtifact:
    """Result of fetching an artifact from a source."""

    artifact_id: str
    target_dir: Path
    files: tuple[Path, ...]
    total_size_bytes: int
    sha256: str


@runtime_checkable
class ArtifactSource(Protocol):
    """Protocol for artifact sources (bundled, HTTP, future local import)."""

    source_kind: str

    async def fetch(self, artifact: ArtifactEntry, target_dir: Path) -> FetchedArtifact:
        """Fetch an artifact to the target directory."""
        ...


BUNDLED_ARTIFACT_MAP: dict[str, str] = {
    "piper-plus.vi-vn.demo": "mery_tts.catalog.fixtures",
    "kokoro.en-us.af-heart.demo": "mery_tts.catalog.fixtures",
}


class BundledArtifactSource:
    """Artifact source that reads from package resources (no network access)."""

    source_kind = "bundled"

    def __init__(
        self,
        *,
        artifact_package_map: dict[str, str] | None = None,
    ) -> None:
        self._package_map = artifact_package_map or BUNDLED_ARTIFACT_MAP

    async def fetch(self, artifact: ArtifactEntry, target_dir: Path) -> FetchedArtifact:
        package = self._package_map.get(artifact.artifact_id)
        if package is None and artifact.artifact_id.startswith("catalog."):
            package = self._package_map.get(artifact.artifact_id.removeprefix("catalog."))
        if package is None:
            raise ArtifactFetchError(
                f"no bundled package mapping for artifact '{artifact.artifact_id}'"
            )

        target_dir.mkdir(parents=True, exist_ok=True)
        package_files = files(package)
        copied_files: list[Path] = []
        total_size = 0
        hasher = hashlib.sha256()

        for resource in package_files.iterdir():
            if resource.name.startswith("__") or resource.name == "bundled-v1.json":
                continue
            if not resource.is_file():
                continue
            data = resource.read_bytes()
            dest = target_dir / resource.name
            dest.write_bytes(data)
            copied_files.append(dest)
            total_size += len(data)
            hasher.update(data)

        if not copied_files:
            raise ArtifactFetchError(
                f"no files found in bundled package for '{artifact.artifact_id}'"
            )

        return FetchedArtifact(
            artifact_id=artifact.artifact_id,
            target_dir=target_dir,
            files=tuple(sorted(copied_files)),
            total_size_bytes=total_size,
            sha256=hasher.hexdigest(),
        )


class FakeArtifactSource:
    """Test artifact source that injects fake artifacts without touching package resources."""

    source_kind = "fake"

    def __init__(
        self,
        *,
        artifacts: dict[str, dict[str, bytes]] | None = None,
    ) -> None:
        self._artifacts = artifacts or {}

    def register(self, artifact_id: str, files: dict[str, bytes]) -> None:
        self._artifacts[artifact_id] = files

    async def fetch(self, artifact: ArtifactEntry, target_dir: Path) -> FetchedArtifact:
        file_map = self._artifacts.get(artifact.artifact_id)
        if file_map is None:
            raise ArtifactFetchError(
                f"fake source has no data for artifact '{artifact.artifact_id}'"
            )

        target_dir.mkdir(parents=True, exist_ok=True)
        copied_files: list[Path] = []
        total_size = 0
        hasher = hashlib.sha256()

        for filename, data in file_map.items():
            dest = target_dir / filename
            dest.write_bytes(data)
            copied_files.append(dest)
            total_size += len(data)
            hasher.update(data)

        return FetchedArtifact(
            artifact_id=artifact.artifact_id,
            target_dir=target_dir,
            files=tuple(sorted(copied_files)),
            total_size_bytes=total_size,
            sha256=hasher.hexdigest(),
        )


__all__ = [
    "BUNDLED_ARTIFACT_MAP",
    "ArtifactFetchError",
    "ArtifactSource",
    "BundledArtifactSource",
    "FakeArtifactSource",
    "FetchedArtifact",
]

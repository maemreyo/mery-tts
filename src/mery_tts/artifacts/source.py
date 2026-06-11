"""Artifact source abstraction for model install.

ADR-0023: ArtifactSource hides whether bytes come from package resources, HTTP, or
a future local import. BundledArtifactSource covers package resources; HttpArtifactSource
covers remote downloads; DispatchArtifactSource routes between them by URL scheme.
"""

from __future__ import annotations

import hashlib
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Protocol, runtime_checkable

from mery_tts.catalog.normalized import ArtifactEntry
from mery_tts.catalog.schema import Catalog, CatalogFile


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


_PLACEHOLDER_SHA256 = "0" * 64
_HUGGINGFACE_HOSTS = frozenset({
    "huggingface.co",
    "cdn-lfs.huggingface.co",
    "cdn-lfs-us-1.huggingface.co",
})


class HttpArtifactSource:
    """Downloads model files from HTTPS URLs.

    Fetches all files listed in the Catalog for the artifact (not just the primary
    entry), verifying sha256 for each file unless the catalog uses the placeholder
    ``"0" * 64`` to signal that the model's checksum is not yet known.
    """

    source_kind = "http"

    def __init__(
        self,
        catalog: Catalog,
        *,
        allowed_hosts: frozenset[str] | None = None,
        on_progress: Callable[[int, int], None] | None = None,
        local_only: bool = False,
        air_gapped: bool = False,
    ) -> None:
        self._catalog = catalog
        self._allowed_hosts = allowed_hosts if allowed_hosts is not None else _HUGGINGFACE_HOSTS
        self._on_progress = on_progress
        self._local_only = local_only
        self._air_gapped = air_gapped

    def _catalog_files(self, artifact_id: str) -> list[CatalogFile]:
        for model in self._catalog.models:
            if model.model_id == artifact_id:
                return list(model.files)
        return []

    def _validate_url(self, url: str) -> None:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ArtifactFetchError(f"unsupported scheme in URL: {url!r}")
        if parsed.netloc not in self._allowed_hosts:
            raise ArtifactFetchError(
                f"host {parsed.netloc!r} not in allowed hosts: {sorted(self._allowed_hosts)}"
            )

    async def fetch(self, artifact: ArtifactEntry, target_dir: Path) -> FetchedArtifact:
        if self._local_only or self._air_gapped:
            policy = "air_gapped" if self._air_gapped else "local_only"
            raise ArtifactFetchError(f"network_disabled:{policy}:model_download")

        import httpx

        catalog_files = self._catalog_files(artifact.artifact_id)
        if not catalog_files:
            raise ArtifactFetchError(
                f"no catalog files for artifact '{artifact.artifact_id}'"
            )
        downloadable = [f for f in catalog_files if f.download_url]
        if not downloadable:
            raise ArtifactFetchError(
                f"no download_url on any file for artifact '{artifact.artifact_id}'"
            )
        for file in downloadable:
            self._validate_url(file.download_url)  # type: ignore[arg-type]

        target_dir.mkdir(parents=True, exist_ok=True)
        total_expected = sum(f.size_bytes for f in downloadable)
        bytes_done = 0
        copied_files: list[Path] = []
        total_size = 0
        hasher = hashlib.sha256()

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=30.0),
        ) as client:
            for file in downloadable:
                chunks: list[bytes] = []
                async with client.stream("GET", file.download_url) as response:  # type: ignore[arg-type]
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        chunks.append(chunk)
                        bytes_done += len(chunk)
                        if self._on_progress:
                            self._on_progress(bytes_done, total_expected)
                data = b"".join(chunks)

                if file.sha256 != _PLACEHOLDER_SHA256:
                    actual = hashlib.sha256(data).hexdigest()
                    if actual != file.sha256:
                        raise ArtifactFetchError(
                            f"sha256 mismatch for '{file.filename}': "
                            f"expected {file.sha256}, got {actual}"
                        )

                dest = target_dir / file.filename
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


class DispatchArtifactSource:
    """Routes fetch calls to bundled or HTTP source based on download_url scheme."""

    source_kind = "dispatch"

    def __init__(self, bundled: ArtifactSource, http: ArtifactSource) -> None:
        self._bundled = bundled
        self._http = http

    async def fetch(self, artifact: ArtifactEntry, target_dir: Path) -> FetchedArtifact:
        if artifact.download_url.startswith(("https://", "http://")):
            return await self._http.fetch(artifact, target_dir)
        return await self._bundled.fetch(artifact, target_dir)


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
    "DispatchArtifactSource",
    "FakeArtifactSource",
    "FetchedArtifact",
    "HttpArtifactSource",
]

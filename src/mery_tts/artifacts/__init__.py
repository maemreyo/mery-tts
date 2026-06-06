"""Artifact source abstraction for model install."""

from .source import (
    BUNDLED_ARTIFACT_MAP,
    ArtifactFetchError,
    ArtifactSource,
    BundledArtifactSource,
    FakeArtifactSource,
    FetchedArtifact,
)

__all__ = [
    "BUNDLED_ARTIFACT_MAP",
    "ArtifactFetchError",
    "ArtifactSource",
    "BundledArtifactSource",
    "FakeArtifactSource",
    "FetchedArtifact",
]

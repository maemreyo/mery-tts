"""Legacy catalog → CatalogGraph compatibility adapter.

ADR-0023: Converts the legacy bundled Catalog shape (models[].files[]) into runtime
CatalogGraph (engines, entries, artifacts, voices). Install planning consumes CatalogGraph only.
"""

from __future__ import annotations

from mery_tts.catalog.normalized import (
    ArtifactEntry,
    CatalogEntry,
    CatalogGraph,
    CatalogVoice,
    EngineEntry,
)
from mery_tts.catalog.schema import Catalog, CatalogFile, CatalogModel

_ENGINE_DISPLAY_NAMES: dict[str, str] = {
    "piper-plus": "Piper Plus",
    "kokoro": "Kokoro",
}

_FILE_ROLE_TO_CAPABILITY: dict[str, str] = {
    "model": "synthesis",
    "config": "synthesis",
    "voice": "synthesis",
    "embedding": "voice-conversion",
    "reference": "reference-cloning",
}


def _engine_display_name(engine_id: str) -> str:
    fallback = engine_id.replace("-", " ").replace("_", " ").title()
    return _ENGINE_DISPLAY_NAMES.get(engine_id, fallback)


def _model_to_catalog_entry(model: CatalogModel) -> CatalogEntry:
    return CatalogEntry(
        catalog_entry_id=model.model_id,
        engine_id=model.engine_id,
    )


def _model_to_artifact_entry(model: CatalogModel) -> ArtifactEntry:
    total_size = sum(f.size_bytes for f in model.files)
    primary_file = _primary_file(model.files)
    download_url = primary_file.download_url or f"bundled://{model.model_id}"
    return ArtifactEntry(
        artifact_id=model.model_id,
        catalog_entry_id=model.model_id,
        engine_id=model.engine_id,
        size_bytes=total_size if total_size > 0 else 1,
        sha256=primary_file.sha256,
        download_url=download_url,
    )


def _primary_file(files: list[CatalogFile]) -> CatalogFile:
    role_priority = {"model": 0, "voice": 1, "config": 2, "embedding": 3, "reference": 4}
    return min(files, key=lambda f: role_priority.get(f.role, 99))


def _model_to_catalog_voice(model: CatalogModel) -> CatalogVoice:
    capabilities = list({_FILE_ROLE_TO_CAPABILITY.get(f.role, "synthesis") for f in model.files})
    return CatalogVoice(
        voice_id=f"catalog.{model.model_id}",
        catalog_entry_id=model.model_id,
        artifact_id=model.model_id,
        engine_id=model.engine_id,
        language=model.locale,
        display_name=_voice_display_name(model.model_id),
        license=model.license,
        commercial_use=False,
        capabilities=capabilities,
    )


def _voice_display_name(model_id: str) -> str:
    return model_id.replace(".", " ").replace("-", " ").replace("_", " ").title()


def legacy_catalog_to_graph(catalog: Catalog) -> CatalogGraph:
    """Convert a legacy Catalog into a runtime CatalogGraph.

    Each legacy model becomes a catalog entry, artifact, and voice in the graph.
    """
    engines_seen: dict[str, str] = {}
    entries: list[CatalogEntry] = []
    artifacts: list[ArtifactEntry] = []
    voices: list[CatalogVoice] = []

    for model in catalog.models:
        if model.engine_id not in engines_seen:
            engines_seen[model.engine_id] = _engine_display_name(model.engine_id)
        entries.append(_model_to_catalog_entry(model))
        artifacts.append(_model_to_artifact_entry(model))
        voices.append(_model_to_catalog_voice(model))

    engine_list = [
        EngineEntry(engine_id=eid, display_name=name)
        for eid, name in sorted(engines_seen.items())
    ]

    return CatalogGraph(
        engines=engine_list,
        artifacts=artifacts,
        voices=voices,
        entries=entries,
    )


def validate_catalog_graph(graph: CatalogGraph) -> list[str]:
    """Validate a CatalogGraph and return a list of issues (empty if valid)."""
    issues: list[str] = []
    entry_ids = [e.catalog_entry_id for e in graph.entries]
    artifact_ids = [a.artifact_id for a in graph.artifacts]
    voice_ids = [v.voice_id for v in graph.voices]

    if len(entry_ids) != len(set(entry_ids)):
        issues.append("duplicate catalogEntryId values")
    if len(artifact_ids) != len(set(artifact_ids)):
        issues.append("duplicate artifactId values")
    if len(voice_ids) != len(set(voice_ids)):
        issues.append("duplicate voiceId values")

    engine_ids = {e.engine_id for e in graph.engines}
    entry_id_set = set(entry_ids)
    artifact_id_set = set(artifact_ids)

    for entry in graph.entries:
        if entry.engine_id not in engine_ids:
            issues.append(f"entry '{entry.catalog_entry_id}' references missing engine")
    for artifact in graph.artifacts:
        if artifact.catalog_entry_id not in entry_id_set:
            issues.append(f"artifact '{artifact.artifact_id}' references missing entry")
        if artifact.engine_id not in engine_ids:
            issues.append(f"artifact '{artifact.artifact_id}' references missing engine")
    for voice in graph.voices:
        if voice.catalog_entry_id not in entry_id_set:
            issues.append(f"voice '{voice.voice_id}' references missing entry")
        if voice.artifact_id not in artifact_id_set:
            issues.append(f"voice '{voice.voice_id}' references missing artifact")
        if voice.engine_id not in engine_ids:
            issues.append(f"voice '{voice.voice_id}' references missing engine")

    return issues


__all__ = [
    "legacy_catalog_to_graph",
    "validate_catalog_graph",
]

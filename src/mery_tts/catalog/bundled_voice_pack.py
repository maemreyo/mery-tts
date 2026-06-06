"""Bundled catalog → VoicePackGraph projection (ADR-0027).

Converts the bundled legacy ``Catalog`` (model + files) into a ``VoicePackGraph``
so that the setup, voice-packs, and provider-runtime APIs can expose real data
instead of an empty graph.

Grouping rule:
    - One ``VoicePack`` per locale in the catalog
    - Pack aggregates every voice in that locale and its required artifacts/runtimes
    - Each unique engine becomes one ``ProviderRuntimeRequirement`` with
      ``install_mode="guided"`` to match the in-tree Piper/Kokoro installers
    - Pack ``use_case`` is inferred from each model's ``recommended_uses``,
      preferring non-``offline-test`` values
"""

from __future__ import annotations

from mery_tts.catalog.bundled import load_bundled_catalog
from mery_tts.catalog.graph_adapter import legacy_catalog_to_graph
from mery_tts.catalog.normalized import CatalogGraph, CatalogVoice
from mery_tts.catalog.schema import Catalog
from mery_tts.catalog.voice_pack import (
    ProviderRuntimeRequirement,
    VoicePack,
    VoicePackGraph,
)

_ENGINE_DISPLAY_NAMES: dict[str, str] = {
    "piper-plus": "Piper Plus",
    "kokoro": "Kokoro",
}

_TEST_USE_CASE_MARKERS: frozenset[str] = frozenset({"offline-test", "test", "fixture"})

_DEFAULT_USE_CASE = "general"
_DEFAULT_INSTALL_MODE = "guided"


def _engine_display_name(engine_id: str) -> str:
    if engine_id in _ENGINE_DISPLAY_NAMES:
        return _ENGINE_DISPLAY_NAMES[engine_id]
    return engine_id.replace("-", " ").replace("_", " ").title()


def _locale_pack_id(locale: str) -> str:
    return f"pack.{locale.lower()}"


def _locale_display_name(locale: str) -> str:
    if not locale or "-" not in locale:
        return locale or "Unknown"
    lang, region = locale.split("-", 1)
    return f"{_language_name(lang)} ({region})"


def _language_name(code: str) -> str:
    known = {
        "en": "English",
        "vi": "Vietnamese",
        "fr": "French",
        "es": "Spanish",
        "de": "German",
        "ja": "Japanese",
        "zh": "Chinese",
    }
    return known.get(code.lower(), code.upper())


def _runtime_id_for_engine(engine_id: str) -> str:
    return f"{engine_id}-runtime"


def _infer_use_case(catalog: Catalog, catalog_entry_id: str) -> str:
    """Pick the most user-meaningful use_case from recommended_uses.

    Prefers non-test markers so the displayed intent matches what a real
    Zam Reader / user would request.
    """
    for model in catalog.models:
        if model.model_id == catalog_entry_id:
            for use in model.recommended_uses:
                if use not in _TEST_USE_CASE_MARKERS:
                    return use
            if model.recommended_uses:
                return model.recommended_uses[0]
            return _DEFAULT_USE_CASE
    return _DEFAULT_USE_CASE


def _voices_by_locale(graph: CatalogGraph) -> dict[str, list[CatalogVoice]]:
    grouped: dict[str, list[CatalogVoice]] = {}
    for voice in graph.voices:
        grouped.setdefault(voice.language, []).append(voice)
    return grouped


def _build_provider_runtime(voice: CatalogVoice) -> ProviderRuntimeRequirement:
    return ProviderRuntimeRequirement(
        provider_runtime_id=_runtime_id_for_engine(voice.engine_id),
        engine_id=voice.engine_id,
        display_name=_engine_display_name(voice.engine_id),
        install_mode=_DEFAULT_INSTALL_MODE,
    )


def _build_voice_pack(
    *,
    locale: str,
    voices: list[CatalogVoice],
    catalog: Catalog,
    graph: CatalogGraph,
) -> VoicePack:
    artifacts_by_id = {artifact.artifact_id: artifact for artifact in graph.artifacts}
    artifact_ids: list[str] = []
    provider_runtime_ids: list[str] = []
    estimated_size = 0
    for voice in voices:
        if voice.artifact_id not in artifact_ids:
            artifact_ids.append(voice.artifact_id)
        runtime_id = _runtime_id_for_engine(voice.engine_id)
        if runtime_id not in provider_runtime_ids:
            provider_runtime_ids.append(runtime_id)
        artifact = artifacts_by_id.get(voice.artifact_id)
        if artifact is not None:
            estimated_size += artifact.size_bytes

    use_case = _infer_use_case(catalog, voices[0].catalog_entry_id)
    pack_id = _locale_pack_id(locale)
    display_name = _locale_display_name(locale)

    return VoicePack(
        voice_pack_id=pack_id,
        display_name=display_name,
        description=f"{display_name} voice pack with {len(voices)} voice(s).",
        locale=locale,
        use_case=use_case,
        voice_ids=[voice.voice_id for voice in voices],
        artifact_ids=artifact_ids,
        provider_runtime_ids=provider_runtime_ids,
        estimated_size_bytes=estimated_size,
        recommended=True,
    )


def bundled_catalog_to_voice_pack_graph(
    catalog: Catalog | None = None,
) -> VoicePackGraph:
    """Project the bundled ``Catalog`` into a ``VoicePackGraph``.

    Returns an empty ``VoicePackGraph`` if the catalog has no models.
    Deterministic: identical input yields identical output.
    """
    active_catalog = catalog if catalog is not None else load_bundled_catalog()
    if not active_catalog.models:
        return VoicePackGraph()

    graph = legacy_catalog_to_graph(active_catalog)
    grouped = _voices_by_locale(graph)

    voice_packs: list[VoicePack] = []
    provider_runtimes: dict[str, ProviderRuntimeRequirement] = {}

    for locale in sorted(grouped):
        voices = grouped[locale]
        voice_packs.append(
            _build_voice_pack(
                locale=locale,
                voices=voices,
                catalog=active_catalog,
                graph=graph,
            )
        )
        for voice in voices:
            runtime_id = _runtime_id_for_engine(voice.engine_id)
            if runtime_id not in provider_runtimes:
                provider_runtimes[runtime_id] = _build_provider_runtime(voice)

    return VoicePackGraph(
        voice_packs=voice_packs,
        provider_runtimes=list(provider_runtimes.values()),
    )


__all__ = [
    "bundled_catalog_to_voice_pack_graph",
]

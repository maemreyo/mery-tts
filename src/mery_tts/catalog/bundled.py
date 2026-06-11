from importlib.resources import files

from mery_tts.catalog.schema import Catalog
from mery_tts.schemas.v1 import VoiceSummary

BUNDLED_CATALOG_RESOURCE = "bundled-v1.json"


def load_bundled_catalog() -> Catalog:
    catalog_file = files("mery_tts.catalog.fixtures") / BUNDLED_CATALOG_RESOURCE
    return Catalog.model_validate_json(catalog_file.read_text(encoding="utf-8"))


def bundled_catalog_voice_summaries(catalog: Catalog | None = None) -> list[VoiceSummary]:
    active_catalog = catalog or load_bundled_catalog()
    return [
        VoiceSummary(
            voice_id=f"catalog.{model.model_id}",
            engine_id=model.engine_id,
            display_name=_display_name(model.model_id),
            supported_locales=model.supported_locales or [model.locale],
            risk_class=model.risk_class,
            license_id=model.license_id,
            license_scope=model.license_scope,
            provenance=model.provenance,
            consent_required=model.consent_required,
            consent_status=model.consent_status,
            trust_tier=model.trust_tier or "bundled_curated",
        )
        for model in active_catalog.models
    ]


def _display_name(model_id: str) -> str:
    return model_id.replace(".", " ").replace("-", " ").title()


__all__ = ["BUNDLED_CATALOG_RESOURCE", "bundled_catalog_voice_summaries", "load_bundled_catalog"]

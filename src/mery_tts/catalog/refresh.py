from pathlib import Path

from mery_tts.catalog.schema import Catalog
from mery_tts.catalog.verifier import CatalogVerifier


class CatalogRefreshService:
    def __init__(self, *, storage_dir: Path, public_key: str) -> None:
        self.storage_dir = storage_dir
        self.public_key = public_key
        self.verifier = CatalogVerifier()
        self.remote_catalog_path = storage_dir / "remote-catalog.json"

    def refresh(self, catalog: Catalog, *, signature: str) -> Catalog:
        verified = self.verifier.verify_remote(
            catalog,
            signature=signature,
            public_key=self.public_key,
        )
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        temporary_path = self.remote_catalog_path.with_suffix(".json.tmp")
        temporary_path.write_text(verified.model_dump_json())
        temporary_path.replace(self.remote_catalog_path)
        return verified

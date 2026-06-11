import shutil
from pathlib import Path

from mery_tts.catalog.schema import Catalog
from mery_tts.catalog.verifier import CatalogVerifier, VerificationError


class CatalogRefreshService:
    def __init__(
        self,
        *,
        storage_dir: Path,
        public_key: str,
        local_only: bool = False,
        air_gapped: bool = False,
    ) -> None:
        self.storage_dir = storage_dir
        self.public_key = public_key
        self.local_only = local_only
        self.air_gapped = air_gapped
        self.verifier = CatalogVerifier()
        self.remote_catalog_path = storage_dir / "remote-catalog.json"
        self.previous_catalog_path = storage_dir / "remote-catalog.previous.json"

    def refresh(self, catalog: Catalog, *, signature: str) -> Catalog:
        if self.local_only or self.air_gapped:
            policy = "air_gapped" if self.air_gapped else "local_only"
            raise VerificationError(f"network_disabled:{policy}:catalog_refresh")
        verified = self.verifier.verify_remote(
            catalog,
            signature=signature,
            public_key=self.public_key,
        )
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        temporary_path = self.remote_catalog_path.with_suffix(".json.tmp")
        temporary_path.write_text(verified.model_dump_json())
        if self.remote_catalog_path.exists():
            shutil.copy2(self.remote_catalog_path, self.previous_catalog_path)
        temporary_path.replace(self.remote_catalog_path)
        return verified

    def rollback_to_previous_valid(self) -> Catalog:
        if not self.previous_catalog_path.exists():
            raise VerificationError("previous_catalog_not_found")
        previous = Catalog.model_validate_json(self.previous_catalog_path.read_text())
        temporary_path = self.remote_catalog_path.with_suffix(".json.rollback.tmp")
        temporary_path.write_text(previous.model_dump_json())
        temporary_path.replace(self.remote_catalog_path)
        return previous

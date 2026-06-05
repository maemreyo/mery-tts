import hashlib
import shutil
from pathlib import Path
from urllib.parse import urlparse

from mery_tts.catalog.schema import Catalog, CatalogModel
from mery_tts.security.guards import reject_unsafe_identifier


class InstallError(ValueError):
    pass


class CatalogInstaller:
    def __init__(self, *, catalog: Catalog, install_root: Path, allowed_hosts: set[str]) -> None:
        self.catalog = catalog
        self.install_root = install_root
        self.allowed_hosts = allowed_hosts

    def install(self, model_id: str, *, downloads: dict[str, bytes]) -> Path:
        safe_model_id = reject_unsafe_identifier(model_id)
        model = self._model_for(safe_model_id)
        target_dir = self.install_root / model.engine_id / model.model_id
        temporary_dir = self.install_root / model.engine_id / f"{model.model_id}.tmp"
        if temporary_dir.exists():
            shutil.rmtree(temporary_dir)
        temporary_dir.mkdir(parents=True, exist_ok=True)
        try:
            installed_path = self._write_verified_files(model, temporary_dir, downloads)
            if target_dir.exists():
                shutil.rmtree(target_dir)
            temporary_dir.replace(target_dir)
            return target_dir / installed_path.name
        except Exception:
            if temporary_dir.exists():
                shutil.rmtree(temporary_dir)
            raise

    def _model_for(self, model_id: str) -> CatalogModel:
        for model in self.catalog.models:
            if model.model_id == model_id:
                return model
        raise InstallError("model_not_found")

    def _write_verified_files(
        self,
        model: CatalogModel,
        temporary_dir: Path,
        downloads: dict[str, bytes],
    ) -> Path:
        installed_path: Path | None = None
        for file in model.files:
            url = f"https://allowed.example/{file.filename}"
            host = urlparse(url).hostname
            if host not in self.allowed_hosts:
                raise InstallError("disallowed_host")
            data = downloads[url]
            if len(data) != file.size_bytes:
                raise InstallError("size_mismatch")
            if hashlib.sha256(data).hexdigest() != file.sha256:
                raise InstallError("checksum_mismatch")
            installed_path = temporary_dir / file.filename
            installed_path.write_bytes(data)
        if installed_path is None:
            raise InstallError("no_files")
        return installed_path

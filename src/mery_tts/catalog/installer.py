import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from mery_tts.catalog.schema import Catalog, CatalogModel
from mery_tts.security.guards import reject_unsafe_identifier


class InstallError(ValueError):
    pass


@dataclass(frozen=True)
class ModelInstallState:
    model_id: str
    catalog_id: str
    previous_state: str
    current_state: str
    action: str
    path: Path


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

    def ensure_installed(self, model_id: str, *, downloads: dict[str, bytes]) -> ModelInstallState:
        safe_model_id = reject_unsafe_identifier(model_id)
        model = self._model_for(safe_model_id)
        installed_path = self._installed_file_path(model)
        if installed_path.exists() and self._installed_file_is_valid(model, installed_path):
            return ModelInstallState(
                model_id=safe_model_id,
                catalog_id=self.catalog.catalog_id,
                previous_state="installed",
                current_state="installed",
                action="kept_same_version",
                path=installed_path,
            )

        corrupt_dir = self.install_root / model.engine_id / f"{model.model_id}.corrupt"
        target_dir = self.install_root / model.engine_id / model.model_id
        if target_dir.exists():
            if corrupt_dir.exists():
                shutil.rmtree(corrupt_dir)
            target_dir.replace(corrupt_dir)
        reinstalled_path = self.install(safe_model_id, downloads=downloads)
        if corrupt_dir.exists():
            shutil.rmtree(corrupt_dir)
        return ModelInstallState(
            model_id=safe_model_id,
            catalog_id=self.catalog.catalog_id,
            previous_state="corrupt",
            current_state="installed",
            action="reinstalled_same_version",
            path=reinstalled_path,
        )

    def _model_for(self, model_id: str) -> CatalogModel:
        for model in self.catalog.models:
            if model.model_id == model_id:
                return model
        raise InstallError("model_not_found")

    def _installed_file_path(self, model: CatalogModel) -> Path:
        if not model.files:
            raise InstallError("no_files")
        return self.install_root / model.engine_id / model.model_id / model.files[-1].filename

    def _installed_file_is_valid(self, model: CatalogModel, installed_path: Path) -> bool:
        if not installed_path.exists() or not model.files:
            return False
        file = model.files[-1]
        data = installed_path.read_bytes()
        return len(data) == file.size_bytes and hashlib.sha256(data).hexdigest() == file.sha256

    def _write_verified_files(
        self,
        model: CatalogModel,
        temporary_dir: Path,
        downloads: dict[str, bytes],
    ) -> Path:
        installed_path: Path | None = None
        for file in model.files:
            url = file.download_url
            if url is None:
                raise InstallError("missing_download_url")
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

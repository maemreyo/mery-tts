from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mery_tts.catalog import Catalog, CatalogFile, CatalogModel, CatalogVerifier, VerificationError
from mery_tts.catalog.installer import CatalogInstaller, InstallError
from mery_tts.catalog.refresh import CatalogRefreshService

VOICE_URL = "https://allowed.example/voice.bin"


def catalog_with_file(*, sha256: str, size_bytes: int, source: str = "remote") -> Catalog:
    return Catalog(
        catalog_id="remote",
        generated_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=1),
        models=[
            CatalogModel(
                model_id="kokoro.en-us.demo",
                engine_id="kokoro",
                locale="en-US",
                quality_tier="fixture",
                recommended_uses=["test"],
                license="fixture",
                source=source,
                files=[
                    CatalogFile(
                        role="voice",
                        filename="voice.bin",
                        sha256=sha256,
                        size_bytes=size_bytes,
                    )
                ],
            )
        ],
    )


def test_remote_refresh_stores_verified_catalog_and_does_not_mutate_on_failure(
    tmp_path: Path,
) -> None:
    verifier = CatalogVerifier()
    catalog = catalog_with_file(sha256="0" * 64, size_bytes=1)
    signature = verifier.sign_for_tests(catalog, public_key="key")
    service = CatalogRefreshService(storage_dir=tmp_path, public_key="key")

    service.refresh(catalog, signature=signature)
    stored = (tmp_path / "remote-catalog.json").read_text()

    with pytest.raises(VerificationError):
        service.refresh(catalog, signature="bad")

    assert (tmp_path / "remote-catalog.json").read_text() == stored


def test_catalog_installer_verifies_checksum_size_host_and_rolls_back(tmp_path: Path) -> None:
    data = b"voice"
    sha = __import__("hashlib").sha256(data).hexdigest()
    catalog = catalog_with_file(sha256=sha, size_bytes=len(data))
    installer = CatalogInstaller(
        catalog=catalog,
        install_root=tmp_path,
        allowed_hosts={"allowed.example"},
    )

    installed = installer.install("kokoro.en-us.demo", downloads={VOICE_URL: data})

    assert installed.exists()
    assert installed.read_bytes() == data

    bad_catalog = catalog_with_file(sha256="0" * 64, size_bytes=len(data))
    bad_installer = CatalogInstaller(
        catalog=bad_catalog,
        install_root=tmp_path / "bad",
        allowed_hosts={"allowed.example"},
    )
    with pytest.raises(InstallError, match="checksum_mismatch"):
        bad_installer.install("kokoro.en-us.demo", downloads={VOICE_URL: data})
    assert not (tmp_path / "bad" / "kokoro" / "kokoro.en-us.demo.tmp").exists()


def test_catalog_installer_rejects_disallowed_host(tmp_path: Path) -> None:
    catalog = catalog_with_file(sha256="0" * 64, size_bytes=1)
    installer = CatalogInstaller(
        catalog=catalog,
        install_root=tmp_path,
        allowed_hosts={"other.example"},
    )

    with pytest.raises(InstallError, match="disallowed_host"):
        installer.install("kokoro.en-us.demo", downloads={VOICE_URL: b"x"})

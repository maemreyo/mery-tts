import builtins
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mery_tts.artifacts.source import ArtifactFetchError, HttpArtifactSource
from mery_tts.catalog import Catalog, CatalogFile, CatalogModel, CatalogVerifier, VerificationError
from mery_tts.catalog.installer import CatalogInstaller, InstallError
from mery_tts.catalog.normalized import ArtifactEntry
from mery_tts.catalog.refresh import CatalogRefreshService

VOICE_URL = "https://allowed.example/voice.bin"


def catalog_with_file(
    *,
    sha256: str,
    size_bytes: int,
    source: str = "remote",
    trust_tier: str | None = "trusted_remote",
    catalog_id: str = "remote",
) -> Catalog:
    return Catalog(
        catalog_id=catalog_id,
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
                trust_tier=trust_tier,
                files=[
                    CatalogFile(
                        role="voice",
                        filename="voice.bin",
                        sha256=sha256,
                        size_bytes=size_bytes,
                        download_url=VOICE_URL,
                    )
                ],
            )
        ],
    )


def test_remote_refresh_blocks_when_local_only_without_persisting(tmp_path: Path) -> None:
    verifier = CatalogVerifier()
    catalog = catalog_with_file(sha256="0" * 64, size_bytes=1)
    signature = verifier.sign_for_tests(catalog, public_key="key")
    service = CatalogRefreshService(
        storage_dir=tmp_path,
        public_key="key",
        local_only=True,
        air_gapped=True,
    )

    with pytest.raises(VerificationError, match="network_disabled:air_gapped:catalog_refresh"):
        service.refresh(catalog, signature=signature)

    assert not (tmp_path / "remote-catalog.json").exists()
    assert not (tmp_path / "remote-catalog.json.tmp").exists()


def test_remote_refresh_stores_previous_valid_catalog_and_rolls_back(
    tmp_path: Path,
) -> None:
    verifier = CatalogVerifier()
    service = CatalogRefreshService(storage_dir=tmp_path, public_key="key")
    previous = catalog_with_file(sha256="0" * 64, size_bytes=1, catalog_id="previous")
    current = catalog_with_file(sha256="1" * 64, size_bytes=1, catalog_id="current")

    service.refresh(previous, signature=verifier.sign_for_tests(previous, public_key="key"))
    service.refresh(current, signature=verifier.sign_for_tests(current, public_key="key"))

    assert service.previous_catalog_path.exists()
    current_catalog = Catalog.model_validate_json(service.remote_catalog_path.read_text())
    assert current_catalog.catalog_id == "current"
    restored = service.rollback_to_previous_valid()

    assert restored.catalog_id == "previous"
    restored_catalog = Catalog.model_validate_json(service.remote_catalog_path.read_text())
    assert restored_catalog.catalog_id == "previous"


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


@pytest.mark.asyncio
async def test_http_artifact_source_blocks_downloads_when_local_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    catalog = catalog_with_file(sha256="0" * 64, size_bytes=1)
    source = HttpArtifactSource(catalog=catalog, local_only=True, air_gapped=True)
    artifact = ArtifactEntry(
        artifact_id="kokoro.en-us.demo",
        catalog_entry_id="kokoro.en-us.demo",
        engine_id="kokoro",
        size_bytes=1,
        sha256="0" * 64,
        download_url=VOICE_URL,
    )
    original_import = builtins.__import__
    import_attempts: list[str] = []

    def fail_on_httpx_import(
        name: str,
        globals_: dict[str, object] | None = None,
        locals_: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name == "httpx":
            import_attempts.append(name)
            raise AssertionError("local-only policy imported httpx before blocking network")
        return original_import(name, globals_, locals_, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fail_on_httpx_import)

    with pytest.raises(ArtifactFetchError, match="network_disabled"):
        await source.fetch(artifact, tmp_path / "artifact")

    assert import_attempts == []
    assert not (tmp_path / "artifact").exists()


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


def test_catalog_installer_marks_corrupt_artifact_and_reinstalls_same_version(
    tmp_path: Path,
) -> None:
    data = b"voice"
    sha = __import__("hashlib").sha256(data).hexdigest()
    catalog = catalog_with_file(sha256=sha, size_bytes=len(data), catalog_id="catalog-v1")
    installer = CatalogInstaller(
        catalog=catalog,
        install_root=tmp_path,
        allowed_hosts={"allowed.example"},
    )

    installed = installer.install("kokoro.en-us.demo", downloads={VOICE_URL: data})
    installed.write_bytes(b"corrupt")

    state = installer.ensure_installed("kokoro.en-us.demo", downloads={VOICE_URL: data})

    assert state.model_id == "kokoro.en-us.demo"
    assert state.catalog_id == "catalog-v1"
    assert state.previous_state == "corrupt"
    assert state.current_state == "installed"
    assert state.action == "reinstalled_same_version"
    assert state.path == installed
    assert installed.read_bytes() == data
    assert not (tmp_path / "kokoro" / "kokoro.en-us.demo.corrupt").exists()


def test_catalog_installer_rejects_disallowed_host(tmp_path: Path) -> None:
    catalog = catalog_with_file(sha256="0" * 64, size_bytes=1)
    installer = CatalogInstaller(
        catalog=catalog,
        install_root=tmp_path,
        allowed_hosts={"other.example"},
    )

    with pytest.raises(InstallError, match="disallowed_host"):
        installer.install("kokoro.en-us.demo", downloads={VOICE_URL: b"x"})


def test_install_error_messages_are_safe_generic_codes() -> None:
    """InstallError messages should be safe generic codes without sensitive information."""
    from mery_tts.catalog.installer import InstallError

    safe_codes = [
        "model_not_found",
        "disallowed_host",
        "size_mismatch",
        "checksum_mismatch",
        "no_files",
    ]

    for code in safe_codes:
        error = InstallError(code)
        assert str(error) == code
        assert "/" not in str(error)
        assert "\\" not in str(error)
        assert "http" not in str(error).lower()
        assert "token" not in str(error).lower()
        assert "secret" not in str(error).lower()

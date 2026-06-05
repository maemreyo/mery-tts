from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from mery_tts.catalog import Catalog, CatalogFile, CatalogModel, CatalogVerifier, VerificationError


def valid_catalog() -> Catalog:
    return Catalog(
        catalog_id="bundled-fixture",
        generated_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=1),
        models=[
            CatalogModel(
                model_id="piper-plus.vi-vn.demo",
                engine_id="piper-plus",
                locale="vi-VN",
                quality_tier="fixture",
                recommended_uses=["offline-test"],
                license="fixture-only",
                source="bundled",
                files=[
                    CatalogFile(
                        role="model",
                        filename="vi_VN-demo.onnx",
                        sha256="0" * 64,
                        size_bytes=1,
                    )
                ],
            )
        ],
    )


def test_bundled_catalog_validates_schema_and_expiry_without_signature() -> None:
    catalog = valid_catalog()

    assert CatalogVerifier().verify_bundled(catalog).catalog_id == "bundled-fixture"


def test_expired_catalog_is_rejected() -> None:
    catalog = valid_catalog().model_copy(
        update={"expires_at": datetime.now(UTC) - timedelta(days=1)}
    )

    with pytest.raises(VerificationError, match="expired"):
        CatalogVerifier().verify_bundled(catalog)


def test_schema_mismatch_is_rejected() -> None:
    with pytest.raises(ValidationError):
        CatalogModel(
            model_id="bad",
            engine_id="piper-plus",
            locale="vietnamese",
            quality_tier="fixture",
            recommended_uses=[],
            license="fixture-only",
            source="bundled",
            files=[],
        )


def test_remote_catalog_requires_matching_signature_and_key() -> None:
    catalog = valid_catalog()
    verifier = CatalogVerifier()
    signature = verifier.sign_for_tests(catalog, public_key="test-key")

    assert verifier.verify_remote(catalog, signature=signature, public_key="test-key") == catalog
    with pytest.raises(VerificationError, match="invalid signature"):
        verifier.verify_remote(catalog, signature="wrong", public_key="test-key")
    with pytest.raises(VerificationError, match="invalid signature"):
        verifier.verify_remote(catalog, signature=signature, public_key="wrong-key")

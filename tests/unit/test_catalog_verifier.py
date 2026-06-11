from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from mery_tts.catalog import Catalog, CatalogFile, CatalogModel, CatalogVerifier, VerificationError
from mery_tts.catalog.verifier import community_catalog_disabled_error


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
    assert catalog.models[0].trust_tier is None


def test_bundled_catalog_rejects_non_curated_trust_tier() -> None:
    community_model = valid_catalog().models[0].model_copy(update={"trust_tier": "community"})
    catalog = valid_catalog().model_copy(update={"models": [community_model]})

    with pytest.raises(VerificationError, match=r"catalog\.community_disabled"):
        CatalogVerifier().verify_bundled(catalog)


def test_expired_catalog_is_rejected() -> None:
    catalog = valid_catalog().model_copy(
        update={"expires_at": datetime.now(UTC) - timedelta(days=1)}
    )

    with pytest.raises(VerificationError, match="expired"):
        CatalogVerifier().verify_bundled(catalog)


@pytest.mark.parametrize(
    "risk_class",
    ["stock", "designed", "reference", "cloned", "dialogue", "conversion"],
)
def test_catalog_model_accepts_voice_risk_classes(risk_class: str) -> None:
    model = CatalogModel(
        model_id=f"piper-plus.en-us.{risk_class}",
        engine_id="piper-plus",
        locale="en-US",
        quality_tier="fixture",
        recommended_uses=["offline-test"],
        license="fixture-only",
        source="bundled",
        files=[],
        risk_class=risk_class,
        license_id="license.fixture",
        license_scope="offline-local-use",
        provenance="fixture catalog",
        consent_required=risk_class != "stock",
        consent_status="pending" if risk_class != "stock" else "not_required",
    )

    assert model.risk_class == risk_class
    assert model.license_id == "license.fixture"
    assert model.license_scope == "offline-local-use"
    assert model.provenance == "fixture catalog"


def test_catalog_model_defaults_missing_governance_to_stock() -> None:
    model = valid_catalog().models[0]

    assert model.risk_class == "stock"
    assert model.license_id is None
    assert model.license_scope is None
    assert model.provenance is None
    assert model.consent_required is False
    assert model.consent_status == "not_required"


def test_catalog_model_rejects_unknown_risk_class() -> None:
    with pytest.raises(ValidationError):
        CatalogModel(
            model_id="piper-plus.en-us.invalid",
            engine_id="piper-plus",
            locale="en-US",
            quality_tier="fixture",
            recommended_uses=[],
            license="fixture-only",
            source="bundled",
            files=[],
            risk_class="celebrity",
        )


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


def test_remote_catalog_requires_matching_signature_key_and_trusted_tier() -> None:
    catalog = Catalog(
        catalog_id="remote-fixture",
        generated_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=1),
        models=[
            valid_catalog().models[0].model_copy(
                update={"source": "remote", "trust_tier": "trusted_remote"}
            )
        ],
    )
    verifier = CatalogVerifier()
    signature = verifier.sign_for_tests(catalog, public_key="test-key")

    assert verifier.verify_remote(catalog, signature=signature, public_key="test-key") == catalog
    with pytest.raises(VerificationError, match="invalid signature"):
        verifier.verify_remote(catalog, signature="wrong", public_key="test-key")
    with pytest.raises(VerificationError, match="invalid signature"):
        verifier.verify_remote(catalog, signature=signature, public_key="wrong-key")


def test_community_catalog_disabled_error_is_structured_and_sanitized() -> None:
    error = community_catalog_disabled_error(request_id="req-community")

    assert error.code.value == "catalog.community_disabled"
    assert error.category.value == "catalog"
    assert error.fallback_policy.value == "disable_feature"
    assert error.recoverability.value == "user_action"
    assert error.sanitized_diagnostic == (
        "audit_trail_required=True,checksum_verification_required=True,"
        "license_metadata_required=True,provenance_metadata_required=True,"
        "reason=community_catalog_disabled,signature_validation_required=True,"
        "takedown_identifier_required=True"
    )


def test_remote_catalog_rejects_missing_or_community_trust_tier() -> None:
    verifier = CatalogVerifier()
    missing_tier = Catalog(
        catalog_id="remote-fixture",
        generated_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=1),
        models=[valid_catalog().models[0].model_copy(update={"source": "remote"})],
    )
    community = Catalog(
        catalog_id="community-fixture",
        generated_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=1),
        models=[
            valid_catalog().models[0].model_copy(
                update={"source": "remote", "trust_tier": "community"}
            )
        ],
    )

    with pytest.raises(VerificationError, match="trust tier mismatch"):
        verifier.verify_remote(
            missing_tier,
            signature=verifier.sign_for_tests(missing_tier, public_key="test-key"),
            public_key="test-key",
        )
    with pytest.raises(VerificationError, match=r"catalog\.community_disabled"):
        verifier.verify_remote(
            community,
            signature=verifier.sign_for_tests(community, public_key="test-key"),
            public_key="test-key",
        )

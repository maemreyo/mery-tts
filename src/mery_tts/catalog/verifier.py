import hashlib
import hmac
from datetime import UTC, datetime

from mery_tts.catalog.schema import Catalog
from mery_tts.errors import ErrorCategory, ErrorCode, LocalTTSError, diagnostic_error


class VerificationError(ValueError):
    pass


def community_catalog_disabled_error(*, request_id: str) -> LocalTTSError:
    return diagnostic_error(
        code=ErrorCode.CATALOG_COMMUNITY_DISABLED,
        category=ErrorCategory.CATALOG,
        request_id=request_id,
        diagnostic={
            "reason": "community_catalog_disabled",
            "signature_validation_required": True,
            "provenance_metadata_required": True,
            "license_metadata_required": True,
            "takedown_identifier_required": True,
            "checksum_verification_required": True,
            "audit_trail_required": True,
        },
    )


class CatalogVerifier:
    def verify_bundled(self, catalog: Catalog) -> Catalog:
        self._ensure_not_expired(catalog)
        self._ensure_trust_tier(catalog, source="bundled", trust_tier="bundled_curated")
        return catalog

    def verify_remote(self, catalog: Catalog, *, signature: str, public_key: str) -> Catalog:
        self._ensure_not_expired(catalog)
        self._ensure_trust_tier(catalog, source="remote", trust_tier="trusted_remote")
        expected = self.sign_for_tests(catalog, public_key=public_key)
        if not hmac.compare_digest(signature, expected):
            raise VerificationError("invalid signature")
        return catalog

    def sign_for_tests(self, catalog: Catalog, *, public_key: str) -> str:
        canonical = catalog.model_dump_json(exclude_none=True, by_alias=True)
        return hashlib.sha256(f"{public_key}:{canonical}".encode()).hexdigest()

    def _ensure_trust_tier(self, catalog: Catalog, *, source: str, trust_tier: str) -> None:
        for model in catalog.models:
            effective_tier = model.trust_tier or "bundled_curated"
            if effective_tier == "community":
                raise VerificationError(str(community_catalog_disabled_error(request_id="catalog")))
            if model.source != source or effective_tier != trust_tier:
                raise VerificationError("catalog trust tier mismatch")

    def _ensure_not_expired(self, catalog: Catalog) -> None:
        expires_at = catalog.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= datetime.now(UTC):
            raise VerificationError("catalog expired")

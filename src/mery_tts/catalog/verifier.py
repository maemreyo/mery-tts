import hashlib
import hmac
from datetime import UTC, datetime

from mery_tts.catalog.schema import Catalog


class VerificationError(ValueError):
    pass


class CatalogVerifier:
    def verify_bundled(self, catalog: Catalog) -> Catalog:
        self._ensure_not_expired(catalog)
        return catalog

    def verify_remote(self, catalog: Catalog, *, signature: str, public_key: str) -> Catalog:
        self._ensure_not_expired(catalog)
        expected = self.sign_for_tests(catalog, public_key=public_key)
        if not hmac.compare_digest(signature, expected):
            raise VerificationError("invalid signature")
        return catalog

    def sign_for_tests(self, catalog: Catalog, *, public_key: str) -> str:
        canonical = catalog.model_dump_json(exclude_none=True, by_alias=True)
        return hashlib.sha256(f"{public_key}:{canonical}".encode()).hexdigest()

    def _ensure_not_expired(self, catalog: Catalog) -> None:
        expires_at = catalog.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= datetime.now(UTC):
            raise VerificationError("catalog expired")

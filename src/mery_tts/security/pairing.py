import secrets
import string
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from mery_tts.errors import (
    ErrorCategory,
    ErrorCode,
    ErrorRecoverability,
    ErrorSeverity,
    FallbackPolicy,
    LocalTTSError,
    RecommendedAction,
)
from mery_tts.security.config import HelperConfig, HelperConfigStore

PAIRING_TTL = timedelta(minutes=10)
PAIRING_ALPHABET = string.ascii_uppercase + string.digits


@dataclass(frozen=True, slots=True)
class PairingChallenge:
    code: str
    setup_url: str
    expires_at: datetime

    def safe_metadata(self) -> dict[str, str]:
        return {"expires_at": self.expires_at.isoformat()}


@dataclass(frozen=True, slots=True)
class PairingClaimResult:
    schema_version: str
    helper_id: str
    port: int
    auth_token: str
    contract_version: str
    capabilities: list[str]
    error: LocalTTSError | None = None


class PairingService:
    def __init__(self, *, config_store: HelperConfigStore, config: HelperConfig) -> None:
        self._config_store = config_store
        self._config = config
        self._challenge: PairingChallenge | None = None

    def create_challenge(self, *, now: datetime | None = None) -> PairingChallenge:
        created_at = now or datetime.now(UTC)
        code = "".join(secrets.choice(PAIRING_ALPHABET) for _ in range(6))
        challenge = PairingChallenge(
            code=code,
            setup_url=f"http://127.0.0.1:{self._config.port}/pair",
            expires_at=created_at + PAIRING_TTL,
        )
        self._challenge = challenge
        return challenge

    def claim(self, code: str, *, now: datetime | None = None) -> PairingClaimResult:
        checked_at = now or datetime.now(UTC)
        challenge = self._challenge
        if challenge is None or challenge.code != code or challenge.expires_at <= checked_at:
            return self._failed_claim()
        self._challenge = None
        return PairingClaimResult(
            schema_version="v1",
            helper_id=self._config.helper_id,
            port=self._config.port,
            auth_token=self._config.auth_token,
            contract_version="v1",
            capabilities=["rest", "websocket", "openai-compatible-speech"],
        )

    def rotate_token(self) -> HelperConfig:
        self._config = self._config_store.rotate_token()
        self._challenge = None
        return self._config

    def _failed_claim(self) -> PairingClaimResult:
        return PairingClaimResult(
            schema_version="v1",
            helper_id="",
            port=self._config.port,
            auth_token="",
            contract_version="v1",
            capabilities=[],
            error=LocalTTSError(
                code=ErrorCode.AUTH_TOKEN_INVALID,
                category=ErrorCategory.AUTH,
                severity=ErrorSeverity.ERROR,
                recoverability=ErrorRecoverability.USER_ACTION,
                user_message_key="errors.auth.token_invalid",
                recommended_action=RecommendedAction.PAIR_CLIENT,
                fallback_policy=FallbackPolicy.NONE,
                sanitized_diagnostic="pairing claim failed",
                request_id="local",
                timestamp=datetime.now(UTC),
            ),
        )

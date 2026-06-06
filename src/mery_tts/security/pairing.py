import json
import secrets
import string
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from mery_tts.errors import ErrorCategory, ErrorCode, LocalTTSError, diagnostic_error
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
    def __init__(
        self,
        *,
        config_store: HelperConfigStore,
        config: HelperConfig,
        max_failed_claims: int = 5,
    ) -> None:
        self._config_store = config_store
        self._config = config
        self._challenge: PairingChallenge | None = None
        self._challenge_path = config_store.config_dir / "pairing-challenge.json"
        self._failed_claims = 0
        self._max_failed_claims = max_failed_claims

    def create_challenge(self, *, now: datetime | None = None) -> PairingChallenge:
        created_at = now or datetime.now(UTC)
        code = "".join(secrets.choice(PAIRING_ALPHABET) for _ in range(6))
        challenge = PairingChallenge(
            code=code,
            setup_url=f"http://127.0.0.1:{self._config.port}/pair",
            expires_at=created_at + PAIRING_TTL,
        )
        self._challenge = challenge
        self._write_challenge(challenge)
        return challenge

    def claim(self, code: str, *, now: datetime | None = None) -> PairingClaimResult:
        checked_at = now or datetime.now(UTC)
        challenge = self._challenge or self._load_challenge()
        if self._failed_claims >= self._max_failed_claims:
            return self._rate_limited_claim()
        if challenge is None or challenge.code != code or challenge.expires_at <= checked_at:
            self._failed_claims += 1
            return self._failed_claim()
        self._challenge = None
        self._delete_challenge()
        self._failed_claims = 0
        self._config = self._config_store.load_or_create()
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
        self._delete_challenge()
        self._failed_claims = 0
        return self._config

    def _write_challenge(self, challenge: PairingChallenge) -> None:
        self._challenge_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "code": challenge.code,
            "setup_url": challenge.setup_url,
            "expires_at": challenge.expires_at.isoformat(),
        }
        temp_path = self._challenge_path.with_name(f"{self._challenge_path.name}.tmp")
        temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        temp_path.chmod(0o600)
        temp_path.replace(self._challenge_path)

    def _load_challenge(self) -> PairingChallenge | None:
        if not self._challenge_path.exists():
            return None
        payload = json.loads(self._challenge_path.read_text())
        return PairingChallenge(
            code=str(payload["code"]),
            setup_url=str(payload["setup_url"]),
            expires_at=datetime.fromisoformat(str(payload["expires_at"])),
        )

    def _delete_challenge(self) -> None:
        try:
            self._challenge_path.unlink()
        except FileNotFoundError:
            return

    def _rate_limited_claim(self) -> PairingClaimResult:
        return PairingClaimResult(
            schema_version="v1",
            helper_id="",
            port=self._config.port,
            auth_token="",
            contract_version="v1",
            capabilities=[],
            error=diagnostic_error(
                code=ErrorCode.AUTH_RATE_LIMITED,
                category=ErrorCategory.AUTH,
                request_id="local",
                diagnostic={"reason": "pairing claim rate limited"},
            ),
        )

    def _failed_claim(self) -> PairingClaimResult:
        return PairingClaimResult(
            schema_version="v1",
            helper_id="",
            port=self._config.port,
            auth_token="",
            contract_version="v1",
            capabilities=[],
            error=diagnostic_error(
                code=ErrorCode.AUTH_TOKEN_INVALID,
                category=ErrorCategory.AUTH,
                request_id="local",
                diagnostic={"reason": "pairing claim failed"},
            ),
        )

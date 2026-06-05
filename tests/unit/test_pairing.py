from datetime import UTC, datetime, timedelta

from mery_tts.security.config import HelperConfigStore
from mery_tts.security.pairing import PairingService


def test_pairing_code_creation_has_expiry_and_safe_log_metadata(tmp_path):
    store = HelperConfigStore(tmp_path)
    config = store.load_or_create()
    pairing = PairingService(config_store=store, config=config)

    challenge = pairing.create_challenge(now=datetime(2026, 6, 5, tzinfo=UTC))

    assert 6 <= len(challenge.code) <= 8
    assert challenge.expires_at == datetime(2026, 6, 5, tzinfo=UTC) + timedelta(minutes=10)
    assert challenge.setup_url == "http://127.0.0.1:8765/pair"
    assert challenge.safe_metadata() == {"expires_at": challenge.expires_at.isoformat()}


def test_valid_claim_returns_token_and_invalidates_code(tmp_path):
    store = HelperConfigStore(tmp_path)
    config = store.load_or_create()
    pairing = PairingService(config_store=store, config=config)
    challenge = pairing.create_challenge()

    claimed = pairing.claim(challenge.code)
    reused = pairing.claim(challenge.code)

    assert claimed.auth_token == config.auth_token
    assert claimed.helper_id == config.helper_id
    assert claimed.capabilities == ["rest", "websocket", "openai-compatible-speech"]
    assert reused.error is not None
    assert reused.error.code.value == "auth.token_invalid"


def test_expired_and_wrong_codes_return_auth_errors(tmp_path):
    store = HelperConfigStore(tmp_path)
    config = store.load_or_create()
    pairing = PairingService(config_store=store, config=config)
    challenge = pairing.create_challenge(now=datetime(2026, 6, 5, tzinfo=UTC))

    expired = pairing.claim(challenge.code, now=datetime(2026, 6, 5, 0, 11, tzinfo=UTC))
    wrong = pairing.claim("WRONG1")

    assert expired.error is not None
    assert expired.error.code.value == "auth.token_invalid"
    assert wrong.error is not None
    assert wrong.error.sanitized_diagnostic == "pairing claim failed"


def test_rotation_invalidates_old_token_and_preserves_helper_id(tmp_path):
    store = HelperConfigStore(tmp_path)
    config = store.load_or_create()
    pairing = PairingService(config_store=store, config=config)

    rotated = pairing.rotate_token()

    assert rotated.helper_id == config.helper_id
    assert rotated.auth_token != config.auth_token
    assert store.load_or_create().helper_id == config.helper_id
    assert store.load_or_create().auth_token == rotated.auth_token

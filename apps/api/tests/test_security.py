"""Unit tests for pure-Python password hashing, HS256 JWT, and reset token helpers."""

from security import (
    create_access_token,
    decode_access_token,
    generate_reset_token,
    hash_password,
    hash_reset_token,
    verify_password,
)


def test_password_hash_and_verify() -> None:
    """Hashed passwords verify correctly and reject wrong passwords or malformed hashes."""
    hashed = hash_password("Sup3rS3cret!", iterations=10_000)
    assert hashed.startswith("pbkdf2_sha256$10000$")
    assert verify_password("Sup3rS3cret!", hashed) is True
    assert verify_password("wrong-password", hashed) is False
    assert verify_password("Sup3rS3cret!", "not-a-valid-hash") is False


def test_jwt_create_decode_expiry_and_tampering() -> None:
    """HS256 JWTs round-trip claims and reject wrong secrets, tampering, or expiration."""
    secret = "unit-test-secret"
    token = create_access_token(
        user_id=7,
        email="admin@apolonsoft.dev",
        role="admin",
        secret=secret,
        expires_seconds=60,
        now=1_000,
    )

    payload = decode_access_token(token, secret, now=1_030)
    assert payload is not None
    assert payload["sub"] == "7"
    assert payload["email"] == "admin@apolonsoft.dev"
    assert payload["role"] == "admin"

    # Expired token
    assert decode_access_token(token, secret, now=1_060) is None
    # Wrong secret
    assert decode_access_token(token, "wrong-secret", now=1_030) is None
    # Tampered signature
    assert decode_access_token(token + "x", secret, now=1_030) is None


def test_reset_token_generation_and_hashing() -> None:
    """Generated reset tokens are unique and match SHA-256 hashing."""
    raw1, digest1 = generate_reset_token()
    raw2, digest2 = generate_reset_token()
    assert raw1 != raw2
    assert digest1 != digest2
    assert hash_reset_token(raw1) == digest1
    assert len(digest1) == 64

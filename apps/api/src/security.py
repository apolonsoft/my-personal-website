"""Pure-Python security helpers (PBKDF2-SHA256, HS256 JWT, reset tokens) for Pyodide Workers."""

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Optional

DEFAULT_PBKDF2_ITERATIONS = 200_000
_HASH_SCHEME = "pbkdf2_sha256"


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def hash_password(password: str, iterations: int = DEFAULT_PBKDF2_ITERATIONS) -> str:
    """Hash a plaintext password using PBKDF2-HMAC-SHA256 with a random 16-byte salt."""
    if not password:
        raise ValueError("Password must not be empty.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{_HASH_SCHEME}${iterations}${_b64url_encode(salt)}${_b64url_encode(digest)}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a plaintext password against a PBKDF2-HMAC-SHA256 hash in constant time."""
    if not password or not stored_hash:
        return False
    parts = stored_hash.split("$")
    if len(parts) != 4 or parts[0] != _HASH_SCHEME:
        return False
    try:
        iterations = int(parts[1])
        salt = _b64url_decode(parts[2])
        expected = _b64url_decode(parts[3])
    except (ValueError, TypeError):
        return False
    if iterations <= 0:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(candidate, expected)


def create_access_token(
    *,
    user_id: int,
    email: str,
    role: str,
    secret: str,
    expires_seconds: int = 86_400,
    now: Optional[int] = None,
) -> str:
    """Create a signed HS256 JWT access token."""
    if not secret:
        raise ValueError("JWT signing secret must not be empty.")
    issued_at = int(time.time()) if now is None else int(now)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "iat": issued_at,
        "exp": issued_at + expires_seconds,
    }
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{_b64url_encode(signature)}"


def decode_access_token(
    token: str,
    secret: str,
    *,
    now: Optional[int] = None,
) -> Optional[dict[str, Any]]:
    """Verify an HS256 JWT and return its payload, or None if invalid/expired."""
    if not token or not secret:
        return None
    segments = token.split(".")
    if len(segments) != 3:
        return None
    header_b64, payload_b64, signature_b64 = segments
    try:
        header = json.loads(_b64url_decode(header_b64))
        if header.get("alg") != "HS256":
            return None
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
        provided_sig = _b64url_decode(signature_b64)
        if not hmac.compare_digest(expected_sig, provided_sig):
            return None
        payload = json.loads(_b64url_decode(payload_b64))
    except (ValueError, TypeError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None
    exp = payload.get("exp")
    current_ts = int(time.time()) if now is None else int(now)
    if not isinstance(exp, (int, float)) or exp <= current_ts:
        return None
    return payload


def hash_reset_token(raw_token: str) -> str:
    """Return the SHA-256 hex digest of a password reset token."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_reset_token() -> tuple[str, str]:
    """Generate a URL-safe password reset token and its SHA-256 hex digest."""
    raw = secrets.token_urlsafe(32)
    return raw, hash_reset_token(raw)

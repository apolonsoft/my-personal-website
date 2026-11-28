### Task 01: Pure-Python Security Helpers & Auth/Email Config
- [x] Completed

#### Full Description
Implement zero-dependency, Pyodide-safe password hashing (`PBKDF2-SHA256`), `HS256` JWT signing/verification, and password-reset token hashing in `apps/api/src/security.py`; extend `apps/api/src/config.py` and `.dev.vars.example` with `JWT_SECRET`, `JWT_EXPIRES_SECONDS`, `EMAIL_FROM`, `EMAIL_FROM_NAME`, and `FRONTEND_URL`; and add unit tests in `apps/api/tests/test_security.py`.

#### Technical Instructions
1. Create `apps/api/src/security.py`:
   - `hash_password(password: str, iterations: int = 200_000) -> str` returning `pbkdf2_sha256$<iterations>$<salt_b64>$<digest_b64>`.
   - `verify_password(password: str, stored_hash: str) -> bool` using `hmac.compare_digest` (returns `False` on malformed hashes).
   - `create_access_token(user_id: int, email: str, role: str, secret: str, expires_seconds: int = 86400) -> str` producing an `HS256` JWT with `sub`, `email`, `role`, `iat`, `exp`.
   - `decode_access_token(token: str, secret: str) -> dict[str, Any] | None` verifying format, HMAC signature (constant-time), `alg == "HS256"`, and `exp > now`.
   - `generate_reset_token() -> tuple[str, str]` returning `(raw_token, sha256_hex_digest)` and `hash_reset_token(raw_token: str) -> str`.
2. Update `apps/api/src/config.py` (`Settings` + `get_settings`) to include:
   - `jwt_secret: str` (reads `JWT_SECRET`, falls back to `API_ADMIN_TOKEN`)
   - `jwt_expires_seconds: int` (reads `JWT_EXPIRES_SECONDS`, default `86400`)
   - `email_from: str` (reads `EMAIL_FROM`, default `"noreply@apolonsoft.dev"`)
   - `email_from_name: str` (reads `EMAIL_FROM_NAME`, default `"Apolonsoft"`)
   - `frontend_url: str` (reads `FRONTEND_URL`, default `"https://www.apolonsoft.dev"`)
3. Update `apps/api/.dev.vars.example` with `JWT_SECRET`, `EMAIL_FROM`, and `FRONTEND_URL`.
4. Create `apps/api/tests/test_security.py` testing password hashing/verification, JWT creation/decoding/expiry/tampering, and reset token hashing.

#### Files Touched
- **Created**: `apps/api/src/security.py`, `apps/api/tests/test_security.py`
- **Modified**: `apps/api/src/config.py`, `apps/api/.dev.vars.example`

#### Verification Strategy
```bash
cd apps/api && uv run pytest -v
```

#### Prepared Git Commit
```text
feat(api): add Pyodide-safe PBKDF2/JWT security helpers and auth/email config

- Add src/security.py with stdlib PBKDF2-SHA256 hashing, HS256 JWTs, and SHA-256 reset tokens
- Extend src/config.py and .dev.vars.example with JWT_SECRET, EMAIL_FROM, and FRONTEND_URL
- Add unit tests in tests/test_security.py
```

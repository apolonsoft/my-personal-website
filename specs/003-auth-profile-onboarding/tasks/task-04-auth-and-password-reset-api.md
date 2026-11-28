### Task 04: Auth, Onboarding & Password Reset API Router
- [x] Completed

#### Full Description
Implement `/api/auth` endpoints (`GET /api/auth/onboarding/status`, `POST /api/auth/onboarding`, `POST /api/auth/login`, `POST /api/auth/forgot-password`, `POST /api/auth/reset-password`) in `apps/api/src/routers/auth.py`, register the router in `apps/api/src/main.py`, and add comprehensive pytest integration tests in `apps/api/tests/test_auth.py`.

#### Technical Instructions
1. Create `apps/api/src/routers/auth.py` with prefix `/api/auth`, tags `["auth"]`, all `async def`:
   - `GET /api/auth/onboarding/status` -> `{"initialized": bool}`.
   - `POST /api/auth/onboarding` (201) -> checks 0 users exist (else `409`), hashes password, inserts admin `User`, returns `AuthTokenResponse`.
   - `POST /api/auth/login` -> normalizes email, checks active user + `verify_password`, returns `AuthTokenResponse` (else `401`).
   - `POST /api/auth/forgot-password` -> always returns `200` with generic message; if active user exists, marks prior unused reset tokens used, creates new `PasswordResetToken` (30-min TTL, SHA-256 hash), sends reset email (HTML + plain text) via `EmailSender`.
   - `POST /api/auth/reset-password` -> hashes submitted token, finds matching unused & unexpired `PasswordResetToken` (else `400`), updates user's `password_hash`, marks token `used_at = utcnow()`, returns `200`.
2. Register `auth_router.router` in `apps/api/src/main.py`.
3. Create `apps/api/tests/test_auth.py` testing full onboarding, 409 lock, login, JWT reuse on `/api/posts`, forgot-password anti-enumeration + email delivery, and reset-password (success + expired/reused/invalid rejection).

#### Files Touched
- **Created**: `apps/api/src/routers/auth.py`, `apps/api/tests/test_auth.py`
- **Modified**: `apps/api/src/main.py`

#### Verification Strategy
```bash
cd apps/api && uv run pytest -v
```

#### Prepared Git Commit
```text
feat(api): implement onboarding, login, forgot-password, and reset-password endpoints

- Add /api/auth router with one-time admin onboarding, JWT login, and 30-min single-use password reset flow
- Register auth router in src/main.py
- Add full integration test coverage in tests/test_auth.py
```

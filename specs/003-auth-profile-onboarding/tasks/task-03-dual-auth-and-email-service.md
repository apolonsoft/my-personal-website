### Task 03: Dual JWT/Token Auth & Cloudflare Email Sending Service
- [x] Completed

#### Full Description
Upgrade `apps/api/src/auth.py` so admin endpoints accept either `API_ADMIN_TOKEN` or a valid admin JWT, add `get_current_user` dependency for JWT-authenticated routes, implement `apps/api/src/email_service.py` using Cloudflare's `send_email` binding (`env.EMAIL`) with local console and test fakes, and configure `send_email` in `apps/api/wrangler.jsonc`.

#### Technical Instructions
1. Update `apps/api/src/auth.py`:
   - `get_current_user(request, session, credentials) -> User` validating Bearer JWT and loading the active user (`401` if invalid/expired/inactive).
   - Update `is_admin_authenticated(request, credentials)` so it returns `True` if Bearer token matches `API_ADMIN_TOKEN` OR decodes as a valid `HS256` JWT with `role == "admin"`.
2. Create `apps/api/src/email_service.py`:
   - `EmailMessage` dataclass (`to`, `subject`, `text`, `html`)
   - `EmailSender` Protocol (`async def send(message: EmailMessage) -> None`)
   - `CloudflareEmailSender` calling `env.EMAIL.send(...)` (converting dict via `pyodide.ffi.to_js` when in Pyodide)
   - `ConsoleEmailSender` logging reset links in local dev when `env.EMAIL` is absent
   - `InMemoryEmailSender` for `pytest`
   - `async def get_email_sender(request: Request) -> EmailSender` dependency.
3. Update `apps/api/wrangler.jsonc` with `"send_email": [{ "name": "EMAIL" }]` and vars `EMAIL_FROM`, `EMAIL_FROM_NAME`, `FRONTEND_URL`.
4. Update `apps/api/tests/conftest.py` to provide an `email_sender` (`InMemoryEmailSender`) fixture overriding `get_email_sender`.

#### Files Touched
- **Created**: `apps/api/src/email_service.py`
- **Modified**: `apps/api/src/auth.py`, `apps/api/wrangler.jsonc`, `apps/api/tests/conftest.py`

#### Verification Strategy
```bash
cd apps/api && uv run pytest -v
```

#### Prepared Git Commit
```text
feat(api): add dual JWT/token admin auth and Cloudflare Email Sending service

- Support admin JWTs alongside API_ADMIN_TOKEN in src/auth.py and add get_current_user dependency
- Implement CloudflareEmailSender (send_email binding), ConsoleEmailSender, and InMemoryEmailSender in src/email_service.py
- Add send_email binding and email config vars to apps/api/wrangler.jsonc
```

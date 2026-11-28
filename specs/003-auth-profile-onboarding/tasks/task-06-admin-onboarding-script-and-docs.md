### Task 06: Headless Admin Onboarding Script & Documentation
- [x] Completed

#### Full Description
Create an idempotent CLI script (`apps/api/scripts/seed_admin.py`) for headless default admin user onboarding, add unit tests (`apps/api/tests/test_seed_admin.py`), add a `seed:admin:local` npm script to root `package.json`, and document `JWT_SECRET`, admin onboarding, and Cloudflare Email Sending setup in `README.md`.

#### Technical Instructions
1. Create `apps/api/scripts/seed_admin.py` with `onboard_default_admin(client, email, password, full_name, headline)` (checks `GET /api/auth/onboarding/status`; skips cleanly if already initialized; posts to `/api/auth/onboarding` otherwise) and CLI args / env defaults (`DEFAULT_ADMIN_EMAIL`, `DEFAULT_ADMIN_PASSWORD`, `DEFAULT_ADMIN_NAME`).
2. Create `apps/api/tests/test_seed_admin.py` verifying first-run creation and second-run idempotent skip.
3. Add `"seed:admin:local"` to root `package.json`.
4. Update `README.md` with Auth/Profile endpoints, `JWT_SECRET`, and `npx wrangler email sending enable apolonsoft.dev`.

#### Files Touched
- **Created**: `apps/api/scripts/seed_admin.py`, `apps/api/tests/test_seed_admin.py`
- **Modified**: `package.json`, `README.md`

#### Verification Strategy
```bash
cd apps/api && uv run pytest -v && cd ../.. && ASTRO_TELEMETRY_DISABLED=1 XDG_CONFIG_HOME=/tmp npm run check --workspace=apps/web
```

#### Prepared Git Commit
```text
feat(api): add headless default admin onboarding script and auth/email docs

- Add idempotent scripts/seed_admin.py and tests/test_seed_admin.py
- Add seed:admin:local script to root package.json
- Document JWT_SECRET, admin onboarding, and Cloudflare Email Sending setup in README.md
```

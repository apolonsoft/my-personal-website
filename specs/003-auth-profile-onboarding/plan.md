# Technical Plan: Auth, Password Reset, Profile & Admin Onboarding API

## Pyodide / Cloudflare Python Workers Constraints
- Pure-Python stdlib crypto (`hashlib.pbkdf2_hmac` SHA-256 + `hmac` `HS256` JWT + `secrets.token_urlsafe`) — zero C-extension dependencies.
- All FastAPI routes and dependencies are `async def` to prevent threadpool spawning in Pyodide.
- Cloudflare Email Service binding `"send_email": [{ "name": "EMAIL" }]` in `apps/api/wrangler.jsonc`, sending both `text` and `html` bodies.

## Database Schema (`0002_auth_and_profile`)
- **`users`**: `id`, `email` (unique, indexed), `password_hash`, `role` (`"admin"`), `is_active`, `full_name`, `headline`, `bio`, `avatar_key` (FK -> `image_assets.object_key`), `avatar_url`, `social_links_json`, `created_at`, `updated_at`.
- **`password_reset_tokens`**: `id`, `user_id` (FK -> `users.id`, indexed), `token_hash` (unique, indexed), `expires_at` (indexed), `used_at`, `created_at`.

## REST Endpoints
- `GET /api/auth/onboarding/status`
- `POST /api/auth/onboarding`
- `POST /api/auth/login`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`
- `GET /api/profile`
- `GET /api/profile/me`
- `PATCH /api/profile/me`

## Verification
- `cd apps/api && uv run pytest -v`
- `cd apps/api && uv run alembic upgrade head && rm -f local.db`
- `CI=true XDG_CONFIG_HOME=/tmp npm run db:migrate:local`

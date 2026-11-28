# Feature Specification: Auth, Password Reset, Profile & Admin Onboarding API

## Overview & Problem Statement
`apps/api` currently uses a static `API_ADMIN_TOKEN` for admin writes and has no user accounts, login flow, password recovery, or profile API. To support a full personal website / CMS administration lifecycle on Cloudflare Python Workers, we need:
- Default admin onboarding (one-time API + headless CLI script).
- Email + password login issuing signed `HS256` JWTs (interoperable with existing `API_ADMIN_TOKEN` on `/api/posts` and `/api/images`).
- Forgot-password and reset-password flows backed by Cloudflare Email Sending (`send_email` binding in production, console logging in local dev).
- Public and authenticated Profile endpoints (`GET /api/profile`, `GET /api/profile/me`, `PATCH /api/profile/me`).

## Answered Clarifications
1. **Password reset email delivery:** Cloudflare Email Sending binding (`send_email`) in production + console logging in local dev + in-memory fake in `pytest`.
2. **Default admin onboarding:** Both one-time `POST /api/auth/onboarding` (only active when 0 users exist) and headless CLI script (`apps/api/scripts/seed_admin.py`).
3. **Auth integration:** Signed `HS256` JWTs from login; existing `/api/posts` and `/api/images` admin routes accept EITHER a valid admin JWT OR `API_ADMIN_TOKEN`.
4. **Profile fields & visibility:** `full_name`, `email`, `headline`, `bio`, R2-backed `avatar_key`/`avatar_url`, and `social_links` — public `GET /api/profile` + authenticated `GET/PATCH /api/profile/me`.

## User Stories & Acceptance Criteria
- **US1 (Onboarding):** `GET /api/auth/onboarding/status` reports `{"initialized": false}` when 0 users exist; `POST /api/auth/onboarding` creates the first admin user and returns a JWT; any subsequent call returns `409 Conflict`.
- **US2 (Login & Dual Auth):** `POST /api/auth/login` verifies email + password and returns `{access_token, token_type, expires_in, user}` (or `401`). The returned JWT authorizes `/api/posts` and `/api/images` admin routes alongside `API_ADMIN_TOKEN`.
- **US3 (Forgot & Reset Password):** `POST /api/auth/forgot-password` always returns `200` (preventing email enumeration), persists a SHA-256 hashed 30-min token for active users, and sends an email with both `text` and `html`. `POST /api/auth/reset-password` validates the token, updates the password, marks the token used, and rejects expired/reused/invalid tokens with `400`.
- **US4 (Profile View/Edit):** `GET /api/profile` returns the primary admin's public profile; `GET /api/profile/me` and `PATCH /api/profile/me` require a valid JWT and validate `avatar_key` against `image_assets`.
- **US5 (Headless Onboarding CLI):** `apps/api/scripts/seed_admin.py` idempotently initializes the default admin user.

## Non-Goals
- Frontend login/reset/profile UI in `apps/web`.
- Multi-user self-registration, OAuth/SSO, MFA, or refresh tokens.
- Edge rate limiting (handled at Cloudflare WAF layer).

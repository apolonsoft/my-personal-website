### Task 05: Public & Authenticated Profile API Router
- [x] Completed

#### Full Description
Implement `/api/profile` endpoints (`GET /api/profile` for public site display, `GET /api/profile/me` and `PATCH /api/profile/me` for authenticated admin profile viewing and editing with R2 `avatar_key` validation) in `apps/api/src/routers/profile.py`, register in `apps/api/src/main.py`, and add tests in `apps/api/tests/test_profile.py`.

#### Technical Instructions
1. Create `apps/api/src/routers/profile.py` with prefix `/api/profile`, tags `["profile"]`, all `async def`:
   - `GET /api/profile` -> returns primary active admin's `PublicProfileRead` (`404` if no admin onboarded yet).
   - `GET /api/profile/me` (`Depends(get_current_user)`) -> returns `ProfileRead`.
   - `PATCH /api/profile/me` (`Depends(get_current_user)`) -> applies partial `ProfileUpdate` (`full_name`, `headline`, `bio`, `avatar_key` validated against `image_assets` with auto-resolved `avatar_url`, `avatar_url`, `social_links`, `email` with uniqueness check -> `409`), updates `updated_at`, returns `ProfileRead`.
2. Register `profile.router` in `apps/api/src/main.py`.
3. Create `apps/api/tests/test_profile.py` covering public profile, 404 before onboarding, 401 unauthenticated `/me`, partial edit, R2 `avatar_key` validation, and `social_links` persistence.

#### Files Touched
- **Created**: `apps/api/src/routers/profile.py`, `apps/api/tests/test_profile.py`
- **Modified**: `apps/api/src/main.py`

#### Verification Strategy
```bash
cd apps/api && uv run pytest -v
```

#### Prepared Git Commit
```text
feat(api): add public and authenticated profile view/edit endpoints

- Add GET /api/profile, GET /api/profile/me, and PATCH /api/profile/me in src/routers/profile.py
- Support R2-backed avatar_key validation and structured social_links JSON storage
- Add integration tests in tests/test_profile.py
```

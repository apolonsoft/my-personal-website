### Task 02: User & PasswordResetToken Models + Alembic/D1 Migration 0002
- [x] Completed

#### Full Description
Add `User` and `PasswordResetToken` SQLModel tables and Auth/Profile Pydantic DTOs to `apps/api/src/models.py`, create Alembic revision `0002_auth_and_profile.py`, and export `apps/api/migrations_d1/0002_auth_and_profile.sql`.

#### Technical Instructions
1. Extend `apps/api/src/models.py` with:
   - `User(SQLModel, table=True)` (`__tablename__ = "users"`)
   - `PasswordResetToken(SQLModel, table=True)` (`__tablename__ = "password_reset_tokens"`)
   - DTOs: `OnboardingRequest`, `OnboardingStatusResponse`, `LoginRequest`, `AuthTokenResponse`, `ForgotPasswordRequest`, `ResetPasswordRequest`, `MessageResponse`, `PublicProfileRead`, `ProfileRead`, `ProfileUpdate`.
2. Create Alembic revision `apps/api/alembic/versions/0002_auth_and_profile.py` (`down_revision = "0001_initial_schema"`).
3. Export `apps/api/migrations_d1/0002_auth_and_profile.sql` using `export_d1_migration.py --revision 0001_initial_schema:0002_auth_and_profile`.

#### Files Touched
- **Created**: `apps/api/alembic/versions/0002_auth_and_profile.py`, `apps/api/migrations_d1/0002_auth_and_profile.sql`
- **Modified**: `apps/api/src/models.py`

#### Verification Strategy
```bash
cd apps/api && uv run alembic upgrade head && rm -f local.db && uv run pytest -v && CI=true XDG_CONFIG_HOME=/tmp npx wrangler d1 migrations apply personal-website-db --local
```

#### Prepared Git Commit
```text
feat(api): add User and PasswordResetToken models and migration 0002

- Add User and PasswordResetToken SQLModel tables and Auth/Profile DTOs in src/models.py
- Add Alembic revision 0002_auth_and_profile.py and Wrangler D1 SQL 0002_auth_and_profile.sql
```

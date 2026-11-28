### Task 03: SQLModel Schema, Dual DB Engine & Alembic -> D1 Migrations
- [ ] Pending

#### Full Description
Define the SQLModel database schema (`ImageAsset` and `Post`) and Pydantic API DTOs, implement the dual database session dependency supporting both Cloudflare D1 (`sqlalchemy-cloudflare-d1`) in Workers and standard SQLite in local dev/testing, configure Alembic for SQLModel autogeneration, and create a deterministic export script producing Wrangler-compatible D1 SQL migrations.

#### Technical Instructions
1. Create `apps/api/src/models.py`:
   - `ImageAsset(SQLModel, table=True)` (`__tablename__ = "image_assets"`):
     - `id: int | None = Field(default=None, primary_key=True)`
     - `object_key: str = Field(unique=True, index=True, max_length=512)`
     - `filename: str = Field(max_length=255)`
     - `content_type: str = Field(max_length=128)`
     - `size_bytes: int`
     - `alt_text: str = Field(default="", max_length=500)`
     - `created_at: datetime = Field(default_factory=utcnow)`
   - `Post(SQLModel, table=True)` (`__tablename__ = "posts"`):
     - `id: int | None = Field(default=None, primary_key=True)`
     - `slug: str = Field(unique=True, index=True, max_length=200)`
     - `title: str = Field(max_length=300)`
     - `description: str = Field(max_length=1000)`
     - `content: str`
     - `category: str = Field(index=True, max_length=100)`
     - `hero_image_key: str | None = Field(default=None, foreign_key="image_assets.object_key", max_length=512)`
     - `hero_image_url: str = Field(max_length=1024)`
     - `image_alt: str = Field(default="", max_length=500)`
     - `published: bool = Field(default=True, index=True)`
     - `pub_date: datetime = Field(index=True)`
     - `updated_date: datetime | None = Field(default=None)`
     - `created_at: datetime = Field(default_factory=utcnow)`
   - Pydantic schemas (`SQLModel` non-table models):
     - `PostCreate` (validates slug pattern `^[a-z0-9]+(?:-[a-z0-9]+)*$`)
     - `PostUpdate` (all fields optional for partial `PATCH`)
     - `PostRead` (includes `id`, `slug`, `title`, `description`, `content`, `category`, `hero_image_key`, `hero_image_url`, `image_alt`, `published`, `pub_date`, `updated_date`, `created_at`)
     - `ImageAssetRead` (includes `id`, `object_key`, `filename`, `content_type`, `size_bytes`, `alt_text`, `url`, `created_at`)
2. Create `apps/api/src/database.py`:
   - `get_engine_for_request(request: Request) -> Engine`:
     - Checks `env = request.scope.get("env")`.
     - If `env` has attribute `DB` (Cloudflare Workers D1 binding), uses `sqlalchemy_cloudflare_d1.create_engine_from_binding(env.DB)`.
     - Otherwise falls back to a cached local SQLite engine using `DATABASE_URL` (default `sqlite:///./local.db`, with `connect_args={"check_same_thread": False}`).
   - `get_session(request: Request) -> Generator[Session, None, None]` FastAPI dependency yielding `Session(engine)`.
3. Update `apps/api/src/routers/health.py` to execute a lightweight `SELECT 1` check using `get_session` so `/api/health` verifies database connectivity.
4. Initialize Alembic in `apps/api/`:
   - `apps/api/alembic.ini` pointing `script_location = alembic` and default `sqlalchemy.url = sqlite:///./local.db`.
   - `apps/api/alembic/env.py` importing `SQLModel` and `src.models`, setting `target_metadata = SQLModel.metadata`, and enabling `render_as_batch=True` for SQLite compatibility.
   - Generate initial revision `apps/api/alembic/versions/0001_initial_schema.py` creating `image_assets` and `posts` tables and indexes.
5. Create `apps/api/scripts/export_d1_migration.py`:
   - Runs Alembic offline SQL generation (`alembic upgrade <rev> --sql`) or compiles `upgrade()` DDL against SQLite dialect, strips transactional `BEGIN`/`COMMIT` statements if incompatible with D1 batch execution, and writes numbered SQL files into `apps/api/migrations_d1/`.
   - Generate `apps/api/migrations_d1/0001_initial_schema.sql`.
6. Update `apps/api/wrangler.jsonc` with `"migrations_dir": "migrations_d1"` on the `DB` D1 binding.
7. Update `apps/api/tests/conftest.py` to use an in-memory SQLite engine (`StaticPool`) overriding `get_session`, and add schema/health DB assertions in `test_health.py`.

#### Files Touched
- **Created**:
  - `apps/api/src/models.py`
  - `apps/api/src/database.py`
  - `apps/api/alembic.ini`
  - `apps/api/alembic/env.py`
  - `apps/api/alembic/script.py.mako`
  - `apps/api/alembic/versions/0001_initial_schema.py`
  - `apps/api/scripts/export_d1_migration.py`
  - `apps/api/migrations_d1/0001_initial_schema.sql`
- **Modified**:
  - `apps/api/src/routers/health.py`
  - `apps/api/wrangler.jsonc`
  - `apps/api/tests/conftest.py`
  - `apps/api/tests/test_health.py`

#### Verification Strategy
```bash
cd apps/api && uv run alembic upgrade head && rm -f local.db && uv run pytest -v && npx wrangler d1 migrations apply personal-website-db --local
```
Expected result: Alembic creates tables cleanly, `pytest` passes all tests, and Wrangler applies `0001_initial_schema.sql` to local D1 without SQL errors.

#### Prepared Git Commit
```text
feat(api): add SQLModel schema, dual D1/SQLite engine, and Alembic migrations

- Define ImageAsset and Post SQLModel tables plus Pydantic DTOs in src/models.py
- Add dual database engine supporting Cloudflare D1 bindings and local SQLite in src/database.py
- Configure Alembic with SQLite batch mode and create initial schema migration 0001
- Add export_d1_migration.py and Wrangler D1 migration 0001_initial_schema.sql
- Update /api/health to verify database connectivity
```

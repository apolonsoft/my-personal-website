### Task 04: Blog Posts CRUD API
- [x] Completed

#### Full Description
Implement the Blog Posts REST router (`GET`, `POST`, `PATCH`, `DELETE` under `/api/posts`) backed by SQLModel and the dual D1/SQLite session dependency, enforce Bearer token authentication on all write endpoints and draft visibility requests, register the router in `main.py`, and add thorough pytest integration tests.

#### Technical Instructions
1. Create `apps/api/src/routers/posts.py` with prefix `/api/posts` and tag `["posts"]`:
   - `GET /api/posts`:
     - Query params: `category: str | None = None`, `include_drafts: bool = False`, `limit: int = Query(default=50, ge=1, le=100)`, `offset: int = Query(default=0, ge=0)`.
     - If `include_drafts` is `True`, verify Bearer token via helper/auth check (raise `401` if invalid/missing).
     - Filter `Post.published == True` unless `include_drafts` is `True`; filter `Post.category == category` when provided.
     - Order by `Post.pub_date.desc()`, apply `offset` & `limit`, and return `list[PostRead]`.
   - `GET /api/posts/{slug}`:
     - Query `Post` by `slug`. If missing, raise `404`.
     - If `not post.published`, require valid Bearer auth (or return `404` if unauthenticated to avoid leaking draft existence).
     - Return `PostRead`.
   - `POST /api/posts` (dependency `Depends(require_admin)`, status `201`):
     - Validate `PostCreate` payload.
     - Check for existing post with same `slug` -> raise `409 Conflict` if duplicate.
     - If `hero_image_key` is provided, verify the `ImageAsset` exists in DB (`400 Bad Request` if missing) and auto-populate `hero_image_url` if omitted.
     - Persist `Post` and return `PostRead`.
   - `PATCH /api/posts/{slug}` (dependency `Depends(require_admin)`):
     - Fetch existing post (`404` if missing).
     - Apply only `exclude_unset=True` fields from `PostUpdate`.
     - If `slug` is changed, check uniqueness (`409 Conflict` on collision).
     - Auto-set `updated_date = utcnow()` unless explicitly passed.
     - Commit and return `PostRead`.
   - `DELETE /api/posts/{slug}` (dependency `Depends(require_admin)`, status `204`):
     - Fetch post (`404` if missing), delete, commit, and return `Response(status_code=204)`.
2. Register `posts.router` in `apps/api/src/main.py`.
3. Create `apps/api/tests/test_posts.py` covering:
   - Creating a post (authenticated -> `201`, unauthenticated -> `401`).
   - Duplicate slug creation -> `409`.
   - Listing published posts sorted newest-first, filtering by `category`, pagination `limit`/`offset`.
   - Draft post hidden from `GET /api/posts` and `GET /api/posts/{slug}` without auth, visible with `include_drafts=true` + Bearer token.
   - Updating a post via `PATCH` (`200`, updates `updated_date`).
   - Deleting a post via `DELETE` (`204`, subsequent `GET` returns `404`).

#### Files Touched
- **Created**:
  - `apps/api/src/routers/posts.py`
  - `apps/api/tests/test_posts.py`
- **Modified**:
  - `apps/api/src/main.py`

#### Verification Strategy
```bash
cd apps/api && uv run pytest -v
```
Expected result: All tests in `test_health.py` and `test_posts.py` pass.

#### Prepared Git Commit
```text
feat(api): implement Blog Posts CRUD endpoints with auth and pytest suite

- Add GET/POST/PATCH/DELETE /api/posts routes in src/routers/posts.py
- Enforce Bearer token auth on mutations and draft visibility queries
- Handle duplicate slugs (409), missing posts (404), and optional ImageAsset linking
- Register posts router in main.py and add integration tests in tests/test_posts.py
```

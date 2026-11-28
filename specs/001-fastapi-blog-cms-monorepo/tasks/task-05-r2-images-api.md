### Task 05: Cloudflare R2 Image Storage API
- [x] Completed

#### Full Description
Implement the Cloudflare R2 object storage abstraction (`src/storage.py`) and the `/api/images` REST router (`src/routers/images.py`) for uploading, streaming, and deleting blog images stored in R2 and indexed in D1 (`ImageAsset`), plus complete pytest coverage using an in-memory R2 fake.

#### Technical Instructions
1. Create `apps/api/src/storage.py`:
   - Define a clean storage protocol/interface `ImageStorage` with async methods:
     - `put(key: str, data: bytes, content_type: str) -> None`
     - `get(key: str) -> StoredObject | None` (`bytes`, `content_type`)
     - `delete(key: str) -> bool`
   - Implement `R2ImageStorage(bucket)` wrapping Cloudflare Worker's `env.IMAGES_BUCKET` R2 binding:
     - `await bucket.put(key, data, httpMetadata={"contentType": content_type})`
     - `obj = await bucket.get(key)` -> read bytes via `arrayBuffer()` / `bytes(...)` and extract `httpMetadata.contentType`
     - `await bucket.delete(key)`
   - Implement `InMemoryImageStorage` for unit/integration testing.
   - Provide `get_storage(request: Request) -> ImageStorage` FastAPI dependency extracting `request.scope["env"].IMAGES_BUCKET` in Workers (or raising a clear `503` if unconfigured outside test overrides).
2. Create `apps/api/src/routers/images.py` with prefix `/api/images` and tag `["images"]`:
   - Define allowed MIME types mapping to safe extensions:
     `{"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/avif": ".avif", "image/gif": ".gif"}`.
   - Define `MAX_IMAGE_BYTES = 10 * 1024 * 1024` (10 MB).
   - `POST /api/images` (dependency `Depends(require_admin)`, status `201`):
     - Accept `file: UploadFile = File(...)`, `alt_text: str = Form(default="")`, `object_key: str | None = Form(default=None)`.
     - Validate `file.content_type` in allowlist (else `415 Unsupported Media Type`).
     - Read bytes, reject empty (`400`) or `> MAX_IMAGE_BYTES` (`413 Content Too Large`).
     - Generate sanitized key `uploads/YYYY/MM/<uuid4><ext>` (or validate explicit `object_key` against path traversal `..` and safe character regex).
     - Store bytes in R2 via `storage.put(...)`, insert `ImageAsset` row in D1, and return `ImageAssetRead` including computed `url` (`f"{R2_PUBLIC_BASE_URL}/{key}"` if configured, else `f"/api/images/{key}"`).
   - `GET /api/images/{key:path}` (public):
     - Reject invalid/traversal keys (`400`).
     - Fetch from R2 via `storage.get(key)` (`404` if `None`).
     - Return `Response(content=obj.data, media_type=obj.content_type, headers={"Cache-Control": "public, max-age=31536000, immutable"})`.
   - `DELETE /api/images/{key:path}` (dependency `Depends(require_admin)`, status `204`):
     - Look up `ImageAsset` in DB (`404` if missing), delete from R2 and DB, commit, return `204`.
3. Register `images.router` in `apps/api/src/main.py`.
4. Update `apps/api/tests/conftest.py` to override `get_storage` with a fresh `InMemoryImageStorage` instance per test.
5. Create `apps/api/tests/test_images.py` testing:
   - Valid PNG/WebP/JPEG upload (`201`), D1 metadata creation, and `GET /api/images/{key}` returning matching bytes, `Content-Type`, and `Cache-Control` header.
   - Unauthenticated upload/delete -> `401`.
   - Unsupported MIME (e.g., `text/plain`) -> `415`.
   - Empty file (`400`) and oversized payload (`413`).
   - `DELETE /api/images/{key}` removes from both R2 and DB (`204`, subsequent `GET` returns `404`).

#### Files Touched
- **Created**:
  - `apps/api/src/storage.py`
  - `apps/api/src/routers/images.py`
  - `apps/api/tests/test_images.py`
- **Modified**:
  - `apps/api/src/main.py`
  - `apps/api/tests/conftest.py`

#### Verification Strategy
```bash
cd apps/api && uv run pytest -v
```
Expected result: All tests in `test_health.py`, `test_posts.py`, and `test_images.py` pass.

#### Prepared Git Commit
```text
feat(api): add Cloudflare R2 image upload, delivery, and deletion endpoints

- Add ImageStorage abstraction with R2ImageStorage binding adapter and InMemoryImageStorage test double
- Implement POST/GET/DELETE /api/images with MIME allowlist, 10 MB size limit, and immutable cache headers
- Persist image metadata in D1 image_assets table
- Add pytest coverage in tests/test_images.py
```

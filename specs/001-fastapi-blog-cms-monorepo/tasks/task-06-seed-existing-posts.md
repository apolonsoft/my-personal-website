### Task 06: Content Migration & Seeding Script
- [ ] Pending

#### Full Description
Create an idempotent Python seeding script (`apps/api/scripts/seed_posts.py`) that parses the 4 existing Markdown blog posts in `apps/web/src/content/blog/`, uploads their referenced hero images from `apps/web/public/` to the FastAPI CMS `/api/images` endpoint (into R2 + D1), and creates the corresponding blog posts via `POST /api/posts`—skipping already-seeded slugs so the script can be safely re-run at any time.

#### Technical Instructions
1. Inspect the 4 existing blog posts in `apps/web/src/content/blog/`:
   - `finding-a-type-scale.md`
   - `one-endpoint-for-a-list.md`
   - `sketching-before-the-browser.md`
   - `when-a-component-is-finished.md`
2. Implement `apps/api/scripts/seed_posts.py`:
   - Pure helper `parse_markdown_post(path: Path) -> ParsedPost` that parses YAML-style frontmatter (`title`, `description`, `pubDate`, `updatedDate`, `category`, `heroImage`, `imageAlt`) and extracts the Markdown body cleanly using Python standard library (avoiding unnecessary extra packages in Pyodide/pyproject if trivial, or using `httpx` which is already in dependencies).
   - Pure helper `seed_from_directory(client, blog_dir: Path, public_dir: Path, admin_token: str) -> SeedReport` accepting any `httpx.Client` or FastAPI `TestClient` so it is directly unit-testable.
   - For each `.md`/`.mdx` file:
     - Derive `slug = path.stem`.
     - Check `GET /api/posts/{slug}` — if `200`, record as skipped and continue (idempotent).
     - Resolve local image path (`public_dir / heroImage.lstrip("/")`), detect MIME type (`mimetypes.guess_type`), upload to `POST /api/images` with `object_key=f"seed/{image_path.name}"` (or handle reuse if already uploaded), and capture `object_key` + `url`.
     - `POST /api/posts` with `Authorization: Bearer <admin_token>`, parsed frontmatter, `hero_image_key`, `hero_image_url`, and Markdown `content`.
   - CLI entrypoint (`if __name__ == "__main__":`) accepting `--api-url` (default `http://127.0.0.1:8787`), `--token` (or `API_ADMIN_TOKEN` env var), `--blog-dir`, and `--public-dir`.
3. Create `apps/api/tests/test_seed.py`:
   - Test `parse_markdown_post` against sample frontmatter (quoted strings, dates, optional `updatedDate`).
   - Test `seed_from_directory` against FastAPI `TestClient` with temporary Markdown + PNG fixtures: verify first run creates posts & images, and second run skips duplicates without error.

#### Files Touched
- **Created**:
  - `apps/api/scripts/seed_posts.py`
  - `apps/api/tests/test_seed.py`

#### Verification Strategy
```bash
cd apps/api && uv run pytest -v
```
Expected result: All tests including `test_seed.py` pass cleanly.

#### Prepared Git Commit
```text
feat(api): add idempotent Markdown-to-CMS seeding script and tests

- Add scripts/seed_posts.py to parse existing Astro blog Markdown posts and upload hero images
- Support idempotent re-runs by skipping already-existing post slugs
- Extract testable client interface and add pytest coverage in tests/test_seed.py
```

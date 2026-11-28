# Feature Specification: Astro + FastAPI Blog CMS Monorepo on Cloudflare

## Overview & Problem Statement

The personal website (`my-personal-website`) is currently a single-package Astro 5 website with static Markdown blog posts (`src/content/blog/*.md`) and local images (`public/images/`), deployed as a single Cloudflare Worker (`wrangler.json`).

To support dynamic content management, media storage, and API-driven updates without rebuilding and redeploying the frontend for every new post, the repository needs to evolve into a **Cloudflare-native monorepo** containing:

1. **Frontend (`apps/web`)**: The existing Astro 5 + React + Tailwind CSS site, refactored into a workspace package and integrated with the backend via a Cloudflare Service Binding (with local HTTP fallback).
2. **Backend (`apps/api`)**: A **Python + FastAPI + SQLModel + Alembic** Blog CMS REST API running on **Cloudflare Python Workers** (Pyodide ASGI), backed by **Cloudflare D1** (serverless SQLite) and **Cloudflare R2** (object storage for images).
3. **Automated CI/CD**: A **GitHub Actions** pipeline that runs automated checks, applies database migrations to D1, and deploys both `apps/api` and `apps/web` to Cloudflare on every `git push` to `main`.

---

## Answered Clarifications

| Topic | Decision |
| :--- | :--- |
| **Backend Scope** | Full Blog CMS: store blog posts, metadata, and uploaded images in the database/object storage, exposed via REST API endpoints. |
| **Cloudflare Python + SQLite Runtime** | Cloudflare Python Workers (Pyodide ASGI via `workers.asgi`) + Cloudflare D1 (serverless SQLite accessed via `sqlalchemy-cloudflare-d1`) + Alembic for schema management and SQL migration export applied via `wrangler d1`. |
| **Image Storage** | Cloudflare R2 bucket (`IMAGES_BUCKET`, 10 GB free tier, \$0 egress) accessed via direct Worker binding and served via public API delivery endpoint (with optional custom R2 public URL override). |
| **CI/CD & API Auth** | GitHub Actions workflow deploying both `apps/api` and `apps/web` on push to `main`; Bearer token authentication (`API_ADMIN_TOKEN`) protecting all write/mutation endpoints. |

---

## User Stories & Acceptance Criteria

### US1: Monorepo Layout Without Regression
**As a** developer,  
**I want** the Astro frontend (`apps/web`) and FastAPI backend (`apps/api`) organized in a single monorepo,  
**So that** both services share version control, CI/CD, and local workflows without breaking existing functionality.

**Acceptance Criteria:**
- Root `package.json` configures npm workspaces (`"workspaces": ["apps/web"]`) and convenience scripts.
- All existing Astro files (`src/`, `public/`, `astro.config.mjs`, `package.json`, `tsconfig.json`, `wrangler.json`, `worker-configuration.d.ts`) reside in `apps/web/`.
- Moving the frontend introduces zero functional changes; `npm run check --workspace=apps/web` (`astro build && tsc && wrangler deploy --dry-run`) passes cleanly.

### US2: Blog CMS CRUD API (`SQLModel` + `Alembic` + `Cloudflare D1`)
**As a** site owner,  
**I want** REST API endpoints to create, read, update, and delete blog posts persisted in SQLite (D1 in production, local SQLite in dev/tests),  
**So that** blog content is managed dynamically via API rather than committing Markdown files.

**Acceptance Criteria:**
- `GET /api/health` returns `200 OK` and verifies database connectivity.
- `GET /api/posts` returns published posts sorted by `pub_date DESC`, optionally filtered by `category`. Draft posts (`published=false`) are excluded unless `include_drafts=true` is requested with valid Bearer auth.
- `GET /api/posts/{slug}` returns a single published post or `404 Not Found` (drafts require Bearer auth).
- `POST /api/posts`, `PATCH /api/posts/{slug}`, and `DELETE /api/posts/{slug}` require `Authorization: Bearer <API_ADMIN_TOKEN>` (`401 Unauthorized` if missing/invalid), validate payloads via SQLModel/Pydantic, return `409 Conflict` on duplicate `slug`, and persist changes in SQLite/D1.
- Database schema is defined in SQLModel (`Post`, `ImageAsset`) and versioned via Alembic, with SQL migrations exported for `wrangler d1 migrations apply`.

### US3: Cloudflare R2 Image Upload & Delivery API
**As a** site owner,  
**I want** to upload, retrieve, and delete blog images stored in Cloudflare R2,  
**So that** images are hosted scalably on Cloudflare with zero egress fees and tracked in the database.

**Acceptance Criteria:**
- `POST /api/images` (Bearer-authenticated) accepts multipart image uploads, validates MIME type (`image/jpeg`, `image/png`, `image/webp`, `image/avif`, `image/gif`) and size (max 10 MB), stores bytes in R2 (`IMAGES_BUCKET`), records an `ImageAsset` row in D1, and returns metadata + public URL.
- Invalid MIME types return `415 Unsupported Media Type`; oversized files return `400 Bad Request` or `413 Content Too Large`.
- `GET /api/images/{key:path}` streams the object from R2 with accurate `Content-Type` and `Cache-Control: public, max-age=31536000, immutable` (`404` if missing).
- `DELETE /api/images/{key:path}` (Bearer-authenticated) removes both the R2 object and `ImageAsset` record.

### US4: Content Migration & Idempotent Seeding
**As a** site owner,  
**I want** a script that imports the 4 existing Markdown posts and their hero images into the CMS API,  
**So that** existing site content transitions seamlessly to the database without manual re-entry.

**Acceptance Criteria:**
- `apps/api/scripts/seed_posts.py` parses `finding-a-type-scale.md`, `one-endpoint-for-a-list.md`, `sketching-before-the-browser.md`, and `when-a-component-is-finished.md` from `apps/web/src/content/blog/`.
- Referenced local hero images from `apps/web/public/images/` are uploaded via `POST /api/images`, and posts are created via `POST /api/posts`.
- Re-running the script is idempotent (existing slugs/images are skipped without errors or duplicates).

### US5: Dynamic Astro SSR Integration
**As a** visitor,  
**I want** the homepage, blog index, individual blog post pages, and RSS feed to render live data from the FastAPI backend,  
**So that** newly published posts and uploaded images appear immediately without rebuilding Astro.

**Acceptance Criteria:**
- `apps/web/wrangler.json` defines a Cloudflare Service Binding (`API` -> `my-personal-website-api`).
- `apps/web/src/lib/api.ts` communicates over `Astro.locals.runtime.env.API` in Cloudflare Workers and falls back to `API_URL` (default `http://127.0.0.1:8787`) in local dev.
- `index.astro`, `blog/index.astro`, `blog/[...slug].astro`, and `rss.xml.js` fetch posts from `apps/api` at request time (`prerender = false`).
- Markdown post bodies are rendered and sanitized server-side (`marked` + `sanitize-html`) inside `blog/[...slug].astro`.

### US6: Automated Deploy on Every Git Push
**As a** developer,  
**I want** every push to `main` to run tests, apply D1 migrations, and deploy both Workers automatically,  
**So that** production stays synchronized with the monorepo without manual deployments.

**Acceptance Criteria:**
- `.github/workflows/deploy.yml` runs on `push` to `main` and `pull_request` (and supports `workflow_dispatch`).
- `test-api` job runs `uv run pytest -v` in `apps/api`.
- `test-web` job runs `npm run check --workspace=apps/web`.
- `deploy` job runs only on `push` to `main` after both test jobs succeed: applies remote D1 migrations, deploys `apps/api` via `pywrangler deploy`, and deploys `apps/web` via `wrangler deploy`.

---

## Boundaries & Non-Goals

- **No Admin Web UI**: Content management is performed through the authenticated REST API (and FastAPI OpenAPI `/docs`); a browser-based editor UI is out of scope.
- **No Multi-User Auth / OAuth / RBAC**: Authentication uses a single shared admin Bearer token (`API_ADMIN_TOKEN`).
- **No Cloudflare Image Transformations**: Images are stored and served directly from R2; `/cdn-cgi/image` resizing can be layered later without changing object keys.
- **No Comments, Likes, or View Analytics**: Scope is strictly Blog CMS (posts, metadata, images).
- **Retain Markdown Backup Files**: Existing `apps/web/src/content/blog/*.md` files remain in place as backups until the seeded production database is verified.

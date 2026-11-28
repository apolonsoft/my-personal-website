# Feature Specification: Local Monorepo Development Setup

## Overview & Problem Statement
Running `my-personal-website` locally requires starting both the Python FastAPI Worker (`apps/api` on port `8787`) and the Astro SSR Worker (`apps/web` on port `4321`) against local Cloudflare D1 and R2 emulation. Currently:
- `apps/api/wrangler.jsonc` has `"binding": "personal-website-images"` instead of `"IMAGES_BUCKET"` expected by `apps/api/src/storage.py`.
- `apps/web/src/lib/api.ts` attempts to use `locals.runtime.env.API` even in `astro dev` (where `platformProxy` provides a non-routable stub).
- Root `package.json` only launches `apps/web` and lacks local D1 migration and seeding shortcuts.

## Answered Clarifications
1. **Launch mode:** Single `npm run dev` command at root starting both FastAPI (`8787`) and Astro (`4321`), plus `dev:api` and `dev:web`.
2. **Local DB bootstrap:** Create `apps/api/.dev.vars`, apply local D1 migrations, and seed the 4 existing blog posts & images.
3. **R2 binding alignment:** Standardize `apps/api/wrangler.jsonc` R2 binding to `IMAGES_BUCKET` to match `apps/api/src/storage.py`.

## Acceptance Criteria
- `npm run dev` starts both `[api]` and `[web]` with prefixed logs and shuts both down cleanly on `SIGINT`/`SIGTERM`.
- `http://127.0.0.1:8787/api/health` returns `{"status":"ok","service":"api","database":"ok"}`.
- `http://127.0.0.1:8787/api/posts` returns the 4 seeded posts and `/api/images/seed/...` serves their R2 images.
- `http://localhost:4321/` and `http://localhost:4321/blog/` render live posts and images from the local API.

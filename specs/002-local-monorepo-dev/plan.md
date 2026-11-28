# Technical Plan: Local Monorepo Development Setup

## Changes
1. **Fix R2 Binding (`apps/api/wrangler.jsonc`)**: Set `"binding": "IMAGES_BUCKET"` for `personal-website-images`.
2. **Fix Dev API Routing (`apps/web/src/lib/api.ts`)**: Use `locals.runtime.env.API` only when `!import.meta.env.DEV`; otherwise fetch `http://127.0.0.1:8787` (or `API_URL`).
3. **Monorepo Dev Runner (`scripts/dev.mjs`, `package.json`, `README.md`)**: Zero-dependency Node script spawning `uv run pywrangler dev --port 8787` and `npm run dev --workspace=apps/web`, plus `dev:api`, `dev:web`, `db:migrate:local`, and `seed:local` scripts.
4. **Bootstrap & E2E Verify**: Create `apps/api/.dev.vars`, apply local D1 migrations, start both servers, seed 4 posts, and verify API + Astro SSR endpoints.

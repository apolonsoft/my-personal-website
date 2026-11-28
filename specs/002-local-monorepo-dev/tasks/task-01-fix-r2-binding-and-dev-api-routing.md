### Task 01: Fix R2 Binding & Local Dev API Routing
- [x] Completed

#### Full Description
Align the R2 bucket binding name in `apps/api/wrangler.jsonc` with `apps/api/src/storage.py` (`IMAGES_BUCKET`) and update `apps/web/src/lib/api.ts` so local `astro dev` routes API requests to `http://127.0.0.1:8787` instead of Wrangler's `platformProxy` stub.

#### Technical Instructions
1. In `apps/api/wrangler.jsonc`, change `"binding": "personal-website-images"` to `"binding": "IMAGES_BUCKET"`.
2. In `apps/web/src/lib/api.ts`, update `apiFetch()` to check `!import.meta.env.DEV && serviceBinding` before using `serviceBinding.fetch(...)`, falling back to `getApiBaseUrl(locals)` in local dev.

#### Files Touched
- **Modified**: `apps/api/wrangler.jsonc`, `apps/web/src/lib/api.ts`

#### Verification Strategy
```bash
cd apps/api && uv run pytest -v && cd ../.. && ASTRO_TELEMETRY_DISABLED=1 XDG_CONFIG_HOME=/tmp npm run check --workspace=apps/web
```

#### Prepared Git Commit
```text
fix(dev): align R2 IMAGES_BUCKET binding and use HTTP API URL in astro dev

- Set R2 binding name to IMAGES_BUCKET in apps/api/wrangler.jsonc
- Bypass platformProxy Service Binding stub during import.meta.env.DEV in apps/web/src/lib/api.ts
```

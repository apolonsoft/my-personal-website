### Task 03: Bootstrap Local Env, Migrate D1, Seed & Verify E2E
- [x] Completed

#### Full Description
Create `apps/api/.dev.vars`, apply local D1 migrations, start both local servers, seed the 4 existing Markdown posts and images into local D1 + R2, and verify both API and Astro SSR endpoints respond with live data.

#### Technical Instructions
1. Copy `apps/api/.dev.vars.example` to `apps/api/.dev.vars` (gitignored).
2. Run `CI=true npm run db:migrate:local`.
3. Start `apps/api` (`uv run pywrangler dev --port 8787`) and `apps/web` (`npm run dev:web`), run `npm run seed:local`, and verify `/api/health`, `/api/posts`, `/`, and `/blog/`.

#### Files Touched
- **Created (gitignored, local-only)**: `apps/api/.dev.vars`

#### Verification Strategy
```bash
curl -sf http://127.0.0.1:8787/api/health && curl -sf http://127.0.0.1:8787/api/posts | head -c 200 && curl -sf http://localhost:4321/blog/ | grep -q "Finding a type scale"
```

#### Prepared Git Commit
```text
chore(dev): verify local monorepo bootstrap and seeding workflow

- Verified local D1 migrations, .dev.vars, pywrangler dev, astro dev, and seed_posts.py end-to-end
```

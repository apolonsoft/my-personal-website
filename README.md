# Personal Website Monorepo (Astro + FastAPI on Cloudflare)

A Cloudflare-native monorepo containing:

- **`apps/web`** — Astro 5 + React + Tailwind CSS frontend Worker connected to the backend via a Cloudflare Service Binding (`env.API`).
- **`apps/api`** — Python 3.12 + FastAPI + SQLModel + Alembic Blog CMS backend running on Cloudflare Python Workers (ASGI), backed by **Cloudflare D1** (SQLite) and **Cloudflare R2** (image storage).

---

## Project Structure

```text
my-personal-website/
├── .github/workflows/deploy.yml   # CI/CD: test, migrate D1, deploy api + web on push to main
├── apps/
│   ├── web/                       # Astro SSR Worker
│   └── api/                       # FastAPI + SQLModel + Alembic + D1 + R2 Worker
├── specs/                         # Spec-Kit specifications and task plans
└── package.json                   # Root npm workspace orchestrator
```

---

## Local Development

### 1. First-Time Local Setup

```bash
npm install
cd apps/api && cp .dev.vars.example .dev.vars && uv sync && cd ../..
npm run db:migrate:local
```

### 2. Start Both Backend & Frontend (`npm run dev`)

From the repository root:

```bash
npm run dev
```

This starts:
- **`[api]`** FastAPI Python Worker at `http://127.0.0.1:8787`
- **`[web]`** Astro SSR frontend at `http://localhost:4321`

*(You can also run them individually with `npm run dev:api` and `npm run dev:web`.)*

### 3. Seed Existing Markdown Posts & Images

With `npm run dev` running in another terminal:

```bash
npm run seed:local
```

Or run backend tests:

```bash
cd apps/api && uv run pytest -v
```

---

## Database Migrations (Alembic -> Cloudflare D1)

1. Generate a new Alembic revision after editing `apps/api/src/models.py`:
   ```bash
   cd apps/api
   uv run alembic revision --autogenerate -m "describe change"
   ```
2. Export the SQL migration for Wrangler D1:
   ```bash
   uv run python scripts/export_d1_migration.py --revision head --output migrations_d1/0002_change.sql
   ```
3. Apply locally or remotely:
   ```bash
   npx wrangler d1 migrations apply personal-website-db --local
   npx wrangler d1 migrations apply personal-website-db --remote
   ```

---

## One-Time Cloudflare & GitHub Setup for Auto-Deploy

Every `git push` to `main` triggers `.github/workflows/deploy.yml`, which runs `pytest` and `npm run check --workspace=apps/web`, applies remote D1 migrations, and deploys both `apps/api` and `apps/web`.

Before the first live deployment:

1. **Create Cloudflare D1 Database** and update `database_id` in `apps/api/wrangler.jsonc`:
   ```bash
   npx wrangler d1 create personal-website-db
   ```
2. **Create Cloudflare R2 Bucket**:
   ```bash
   npx wrangler r2 bucket create personal-website-images
   ```
3. **Set Production Admin Token** on the API Worker:
   ```bash
   cd apps/api && npx wrangler secret put API_ADMIN_TOKEN
   ```
4. **Add GitHub Repository Secrets** (`Settings -> Secrets and variables -> Actions`):
   - `CLOUDFLARE_API_TOKEN` (with Workers Scripts Edit, D1 Edit, and Workers R2 Storage Edit permissions)
   - `CLOUDFLARE_ACCOUNT_ID`

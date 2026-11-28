### Task 08: GitHub Actions CI/CD Auto-Deploy on Git Push
- [ ] Pending

#### Full Description
Create the GitHub Actions workflow `.github/workflows/deploy.yml` so every `git push` to `main` automatically validates both the Python FastAPI backend (`pytest`) and Astro frontend (`npm run check`), applies pending D1 SQL migrations remotely, and deploys `apps/api` and `apps/web` to Cloudflare Workers. Also document local development, seeding, and required secrets in `README.md`.

#### Technical Instructions
1. Create `.github/workflows/deploy.yml`:
   - `name: CI & Deploy to Cloudflare`
   - Triggers:
     - `push: branches: [main]`
     - `pull_request: branches: [main]`
     - `workflow_dispatch:`
   - Concurrency group (`deploy-${{ github.ref }}`, `cancel-in-progress: false` on `main`).
   - **Job 1: `test-api`** (`ubuntu-latest`):
     - `actions/checkout@v4`
     - `astral-sh/setup-uv@v5` with `python-version: "3.12"`
     - `working-directory: apps/api`: run `uv sync --frozen` and `uv run pytest -v`.
   - **Job 2: `test-web`** (`ubuntu-latest`):
     - `actions/checkout@v4`
     - `actions/setup-node@v4` with `node-version: "22"`, `cache: "npm"`
     - Run `npm ci` at root and `npm run check --workspace=apps/web`.
   - **Job 3: `deploy`** (`needs: [test-api, test-web]`, `if: github.event_name == 'push' && github.ref == 'refs/heads/main'`):
     - `actions/checkout@v4`
     - `astral-sh/setup-uv@v5` (`python-version: "3.12"`) + `actions/setup-node@v4` (`node-version: "22"`, `cache: "npm"`)
     - Install dependencies: `npm ci` at root and `uv sync --frozen` in `apps/api`.
     - Step 1 — Apply D1 migrations (`working-directory: apps/api`):
       `npx wrangler d1 migrations apply personal-website-db --remote`
       with `CLOUDFLARE_API_TOKEN` & `CLOUDFLARE_ACCOUNT_ID` from `${{ secrets.* }}`.
     - Step 2 — Deploy `apps/api` (`working-directory: apps/api`):
       `uv run pywrangler deploy`
       with `CLOUDFLARE_API_TOKEN` & `CLOUDFLARE_ACCOUNT_ID`.
     - Step 3 — Deploy `apps/web` (root):
       `npm run deploy --workspace=apps/web`
       with `CLOUDFLARE_API_TOKEN` & `CLOUDFLARE_ACCOUNT_ID`.
2. Update `README.md` with clear documentation covering:
   - Monorepo layout (`apps/web`, `apps/api`)
   - Local development commands (`uv run pywrangler dev`, `npm run dev --workspace=apps/web`)
   - Running Alembic -> D1 migrations and `seed_posts.py`
   - Required one-time Cloudflare setup (`d1 create`, `r2 bucket create`, `wrangler secret put API_ADMIN_TOKEN`) and GitHub secrets (`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`).

#### Files Touched
- **Created**:
  - `.github/workflows/deploy.yml`
- **Modified**:
  - `README.md`

#### Verification Strategy
```bash
python3 -c 'import yaml; yaml.safe_load(open(".github/workflows/deploy.yml"))' 2>/dev/null || cd apps/api && uv run python -c 'import pathlib; text = pathlib.Path("../../.github/workflows/deploy.yml").read_text(); assert "pywrangler deploy" in text and "wrangler d1 migrations apply" in text and "apps/web" in text; print("Workflow file verified")'
```
Also run full monorepo checks:
```bash
cd apps/api && uv run pytest -v && cd ../.. && npm run check --workspace=apps/web
```
Expected result: Valid workflow YAML, all backend pytest cases pass, and frontend check passes.

#### Prepared Git Commit
```text
ci(deploy): add GitHub Actions workflow to test and deploy monorepo to Cloudflare

- Add .github/workflows/deploy.yml running pytest and astro check on PRs and pushes
- Apply remote D1 migrations and deploy apps/api and apps/web on push to main
- Document monorepo setup, local dev, seeding, and Cloudflare/GitHub secrets in README.md
```

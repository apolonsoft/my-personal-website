### Task 02: Monorepo Dev Runner & Root Scripts
- [x] Completed

#### Full Description
Add a zero-dependency Node process runner (`scripts/dev.mjs`) and root `package.json` scripts (`dev`, `dev:api`, `dev:web`, `db:migrate:local`, `seed:local`) so both `apps/api` and `apps/web` start with a single `npm run dev` command, and update `README.md`.

#### Technical Instructions
1. Create `scripts/dev.mjs` spawning `uv run pywrangler dev --port 8787` (cwd `apps/api`) and `npm run dev --workspace=apps/web` (cwd root), forwarding `SIGINT`/`SIGTERM` cleanly.
2. Update root `package.json` scripts with `dev`, `dev:api`, `dev:web`, `db:migrate:local`, and `seed:local`.
3. Update `README.md` with the single-command local dev workflow.

#### Files Touched
- **Created**: `scripts/dev.mjs`
- **Modified**: `package.json`, `README.md`

#### Verification Strategy
```bash
node --check scripts/dev.mjs && npm run check --workspace=apps/web
```

#### Prepared Git Commit
```text
feat(dev): add single-command monorepo dev runner and local DB/seed scripts

- Add zero-dependency scripts/dev.mjs to run FastAPI and Astro dev servers together
- Add dev, dev:api, db:migrate:local, and seed:local scripts in root package.json
- Update README.md with local development instructions
```

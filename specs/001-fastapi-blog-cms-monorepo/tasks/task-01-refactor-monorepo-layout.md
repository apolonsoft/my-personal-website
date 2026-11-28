### Task 01: Preparatory Refactor — Monorepo Layout
- [x] Completed

#### Full Description
Reorganize the repository from a single-package Astro layout at the root into a workspace-based monorepo layout by moving the existing Astro application into `apps/web/`, adding a root npm workspaces `package.json`, and updating `.gitignore` for upcoming Python/uv/SQLite artifacts.

Per `.agent/rules/single-file-tasks.md`, this is a **preparatory refactoring task**: it must introduce **ZERO functional changes** to the Astro website and verify that all existing build, TypeScript, and Wrangler dry-run checks still pass identically after the move.

#### Technical Instructions
1. Create `apps/web/` directory.
2. Move all existing Astro source and config files into `apps/web/` using `git mv` (or equivalent clean move):
   - `src/` -> `apps/web/src/`
   - `public/` -> `apps/web/public/`
   - `astro.config.mjs` -> `apps/web/astro.config.mjs`
   - `package.json` -> `apps/web/package.json`
   - `tsconfig.json` -> `apps/web/tsconfig.json`
   - `wrangler.json` -> `apps/web/wrangler.json`
   - `worker-configuration.d.ts` -> `apps/web/worker-configuration.d.ts`
   - Remove root `node_modules/`, `.astro/`, `.wrangler/`, and `dist/` build caches if needed before reinstalling at root workspace.
3. Update `apps/web/package.json` `"name"` to `"@my-personal-website/web"` (keep all scripts and dependencies unchanged).
4. Create root `/package.json` with:
   - `"name": "my-personal-website-monorepo"`
   - `"private": true`
   - `"workspaces": ["apps/web"]`
   - `"engines": { "node": ">=22" }`
   - Convenience scripts forwarding to `apps/web`: `"dev:web"`, `"build:web"`, `"check:web"`, `"deploy:web"`, plus `"dev"`, `"build"`, `"check"` aliases.
5. Update root `.gitignore` to ignore Python/uv/SQLite artifacts (`**/.venv/`, `**/__pycache__/`, `*.pyc`, `.pytest_cache/`, `.uv-cache/`, `*.db`, `*.sqlite3`, `apps/api/.dev.vars`) and workspace-nested build artifacts (`apps/web/dist/`, `apps/web/.astro/`, `apps/web/.wrangler/`).
6. Run `npm install` at root so `package-lock.json` reflects the npm workspace cleanly, and verify `apps/web` builds and passes `check`.

#### Files Touched
- **Moved**:
  - `src/**` -> `apps/web/src/**`
  - `public/**` -> `apps/web/public/**`
  - `astro.config.mjs` -> `apps/web/astro.config.mjs`
  - `tsconfig.json` -> `apps/web/tsconfig.json`
  - `wrangler.json` -> `apps/web/wrangler.json`
  - `worker-configuration.d.ts` -> `apps/web/worker-configuration.d.ts`
  - `package.json` -> `apps/web/package.json` (modified `"name"` for workspace clarity)
- **Created**:
  - `package.json` (root npm workspace orchestrator)
- **Modified**:
  - `.gitignore`
  - `package-lock.json`

#### Verification Strategy
```bash
npm install && npm run check --workspace=apps/web
```
Expected result: `astro build`, `tsc`, and `wrangler deploy --dry-run` all exit with code `0` with zero errors.

#### Prepared Git Commit
```text
refactor(monorepo): move Astro website into apps/web workspace

- Move src/, public/, astro.config.mjs, tsconfig.json, wrangler.json, and worker-configuration.d.ts into apps/web/
- Add root package.json configuring npm workspaces for apps/web
- Update .gitignore with Python, uv, SQLite, and workspace build artifact entries
- Verified unchanged behavior via npm run check --workspace=apps/web
```

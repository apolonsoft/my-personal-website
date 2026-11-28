### Task 07: Astro Frontend Integration with FastAPI CMS
- [x] Completed

#### Full Description
Connect `apps/web` to the `apps/api` FastAPI CMS backend so the homepage (`Recent writing`), `/blog/` index, `/blog/[...slug]/` post pages, and `/rss.xml` feed fetch live posts from D1 via a Cloudflare Service Binding (with local HTTP fallback) and render sanitized Markdown server-side on demand (`prerender = false`).

#### Technical Instructions
1. Update `apps/web/package.json` to add:
   - `"marked"` (Markdown-to-HTML rendering)
   - `"sanitize-html"` and devDependency `"@types/sanitize-html"` (XSS-safe HTML sanitization in SSR)
   Run `npm install` at workspace root to update `package-lock.json`.
2. Update `apps/web/wrangler.json` to add the Cloudflare Service Binding to the backend Worker:
   ```json
   "services": [
     {
       "binding": "API",
       "service": "my-personal-website-api"
     }
   ]
   ```
   Update `apps/web/src/env.d.ts` (and run `npm run cf-typegen --workspace=apps/web` if applicable) so TypeScript knows `Env.API` (`Fetcher`) and optional `API_URL` / `PUBLIC_API_URL`.
3. Update `apps/web/astro.config.mjs`:
   - Keep `adapter: cloudflare({ platformProxy: { enabled: true } })`.
   - Use per-route `export const prerender = false;` on dynamic CMS routes (`/`, `/blog/`, `/blog/[...slug]/`, `/rss.xml.js`) while keeping static pages like `/about/` prerendered (or configure `output: "server"` if cleaner — prefer per-route `prerender = false` on CMS pages so static pages stay fast).
4. Create `apps/web/src/lib/api.ts`:
   - Define `ApiPost` TypeScript interface matching FastAPI `PostRead` (`id`, `slug`, `title`, `description`, `content`, `category`, `hero_image_key`, `hero_image_url`, `image_alt`, `published`, `pub_date`, `updated_date`).
   - Implement `apiFetch(locals: App.Locals, path: string, init?: RequestInit): Promise<Response>`:
     - When `locals?.runtime?.env?.API` exists (Cloudflare Worker runtime), call `locals.runtime.env.API.fetch(new Request(`https://api.internal${path}`, init))`.
     - Otherwise (local `astro dev` / tests), fetch `${import.meta.env.API_URL ?? "http://127.0.0.1:8787"}${path}`.
   - Implement `resolveImageUrl(locals: App.Locals, heroImageUrl: string): string` so relative `/api/images/...` URLs resolve against `PUBLIC_API_URL` (or `http://127.0.0.1:8787` in local dev) when not proxied on the same origin.
5. Update `apps/web/src/lib/posts.ts`:
   - Replace `getCollection("blog")` with `getPosts(locals: App.Locals): Promise<BlogPostItem[]>` and `getPostBySlug(locals: App.Locals, slug: string): Promise<BlogPostItem | null>`.
   - Map API fields (`pub_date` -> `Date`, `hero_image_url`, `image_alt`, etc.) and resolve image URLs cleanly.
6. Update Astro pages and layout:
   - `apps/web/src/pages/index.astro`: add `export const prerender = false;`, call `await getPosts(Astro.locals)` for `recentPosts`.
   - `apps/web/src/pages/blog/index.astro`: add `export const prerender = false;`, call `await getPosts(Astro.locals)`.
   - `apps/web/src/pages/blog/[...slug].astro`: add `export const prerender = false;`, fetch `getPostBySlug(Astro.locals, Astro.params.slug)`, return `Astro.redirect("/404")` or `new Response("Not Found", { status: 404 })` if missing, render `post.content` with `marked.parse` + `sanitizeHtml`, and pass into `BlogPost.astro` via `<Fragment set:html={htmlContent} />`.
   - `apps/web/src/layouts/BlogPost.astro`: update `Props` interface from `CollectionEntry<"blog">["data"]` to a clean `BlogPostLayoutProps` interface decoupled from `astro:content`.
   - `apps/web/src/pages/rss.xml.js`: add `export const prerender = false;`, fetch posts via `getPosts(context.locals)`.
7. Keep `apps/web/src/content/blog/*.md` untouched as backup files until production D1 seeding is verified.

#### Files Touched
- **Created**:
  - `apps/web/src/lib/api.ts`
- **Modified**:
  - `apps/web/package.json`
  - `package-lock.json`
  - `apps/web/wrangler.json`
  - `apps/web/src/env.d.ts`
  - `apps/web/src/lib/posts.ts`
  - `apps/web/src/layouts/BlogPost.astro`
  - `apps/web/src/pages/index.astro`
  - `apps/web/src/pages/blog/index.astro`
  - `apps/web/src/pages/blog/[...slug].astro`
  - `apps/web/src/pages/rss.xml.js`

#### Verification Strategy
```bash
npm run check --workspace=apps/web
```
Expected result: `astro build`, `tsc`, and `wrangler deploy --dry-run` succeed with exit code `0`.

#### Prepared Git Commit
```text
feat(web): integrate Astro frontend with FastAPI CMS via Cloudflare Service Binding

- Add marked and sanitize-html for safe SSR Markdown rendering
- Configure Cloudflare Service Binding API -> my-personal-website-api in wrangler.json
- Add typed API client (Service Binding + local HTTP fallback) in src/lib/api.ts
- Update posts.ts, BlogPost.astro, index.astro, blog pages, and rss.xml.js for dynamic SSR data fetching
```

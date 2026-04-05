# 🔍 LeadIQ — Project Audit & Market-Readiness Checkpoints

> Last audited: 2026-03-26  
> Stack: Next.js 15.3.9 App Router + FastAPI backend + Redis + PostgreSQL

---

## 1. 🌿 Environment Variables

### Frontend (`Next.js`) — `.env.local`

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `NEXT_PUBLIC_API_URL` | Optional | `http://localhost:8000` | URL of the FastAPI backend. Prefix with `NEXT_PUBLIC_` to expose to browser. |

### Backend (`FastAPI`) — `.env` or system env

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `REDIS_URL` | ✅ | `redis://localhost:6379` | Full Redis connection URL |
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://leadiq:leadiq@localhost:5432/leadiq` | PostgreSQL asyncpg URL |
| `ALLOWED_ORIGINS` | ✅ | `["http://localhost:3000"]` | JSON array of CORS allowed origins |
| `DEBUG` | No | `False` | Enable FastAPI debug mode |
| `OPENAI_API_KEY` | Future | — | For Phase 4 LLM integration |
| `SECRET_KEY` | Future | — | For JWT authentication |

---

## 2. ✅ Fixed Issues (this PR)

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| 1 | Missing CSS utility classes (`interactive-scale`, `animate-slide-in-right`, `terminal-window`, `terminal-chrome`, `terminal-dot-*`, `focus-ring`, `custom-scrollbar`) — used in components but never defined | 🔴 Critical | ✅ Fixed — added to `globals.css` |
| 2 | Missing CSS variables `--success`, `--warning`, `--info` (and `*-foreground`) in `:root` and `.dark` — caused `text-success`, `bg-success` etc. to render as transparent | 🔴 Critical | ✅ Fixed — added to `globals.css` |
| 3 | `--accent` CSS variable set to same value as `--secondary` in light mode instead of the purple/violet accent color | 🟡 Medium | ✅ Fixed |
| 4 | `vercel.json` had Vite-era SPA rewrite rule — breaks Next.js deployment | 🔴 Critical | ✅ Fixed — updated to `"framework": "nextjs"` |
| 5 | Duplicate + conflicting CSS variable sets (tokens appended to bottom of globals.css, creating `--color-*` duplicates) | 🟡 Medium | ✅ Fixed — removed duplicates, single source of truth |
| 6 | No `.env.example` file | 🟡 Medium | ✅ Fixed — created `.env.example` |
| 7 | `package.json` missing `"type": "module"` causing Node.js MODULE_TYPELESS_PACKAGE_JSON warning | 🟡 Medium | ✅ Fixed |
| 8 | No `loading.tsx` — pages had no skeleton/loading state | 🟡 Medium | ✅ Fixed — added `src/app/loading.tsx` |
| 9 | No `error.tsx` — uncaught client errors showed blank page | 🟡 Medium | ✅ Fixed — added `src/app/error.tsx` |
| 10 | Security headers missing | 🟡 Medium | ✅ Fixed — added in `next.config.ts` |
| 11 | `robots.txt` had no `Disallow` for API routes; no Sitemap reference | 🟢 Low | ✅ Fixed |
| 12 | `index.html` (Vite root) still in repo root | 🟢 Low | ✅ Fixed — removed |
| 13 | `README.md` was placeholder | 🟢 Low | ✅ Fixed — full documentation written |
| 14 | `next.config.ts` empty — no React strict mode, no compression, no image formats | 🟡 Medium | ✅ Fixed |
| 15 | `postcss.config.js` named `.js` but project is now `"type": "module"` | 🟡 Medium | ✅ Fixed — renamed to `.cjs` |

---

## 3. 🔄 Known Remaining Issues (Not Yet Fixed)

| # | Issue | Severity | Action Required |
|---|-------|----------|-----------------|
| 1 | **First Load JS too large** — `/`, `/pipeline`, `/demand-miner` all load ~317 KB (target: < 200 KB) | 🟡 Medium | Implement dynamic imports for heavy components (`recharts`, `radix-ui`) |
| 2 | **Frontend data is demo-only** — `use-leads` hook never fetches from `/api/leads` | 🟡 Medium | Wire `LeadProvider` to fetch from `NEXT_PUBLIC_API_URL/api/leads` |
| 3 | **No authentication** — any user can access all leads and actions | 🔴 Critical (production) | Implement NextAuth.js or Clerk |
| 4 | **CRM service is in-memory** — `backend/services/crm_service.py` uses a dict, not PostgreSQL | 🟡 Medium | Implement SQLAlchemy session with `asyncpg` |
| 5 | **No real LLM** — AI analyzer uses heuristics, not an actual LLM API | 🟡 Medium | Integrate OpenAI / Anthropic API |
| 6 | **`vite.config.ts` still in repo** — orphaned (only vitest uses it), causes confusion | 🟢 Low | Move vitest config to standalone or remove vite dep entirely |
| 7 | **Mixed lockfiles** — both `bun.lock`, `bun.lockb`, and `package-lock.json` | 🟢 Low | Remove bun lockfiles, standardize on npm |
| 8 | **Duplicate `src/index.css`** — no longer imported anywhere | 🟢 Low | Delete file |
| 9 | **Duplicate `src/styles/tokens.css`** — no longer imported anywhere | 🟢 Low | Delete file |
| 10 | **No rate limiting** on API routes | 🔴 Critical (production) | Add middleware rate limiting |
| 11 | **No input validation** on PATCH `/api/lead/[id]` | 🟡 Medium | Add Zod schema validation |
| 12 | **`npm audit` vulnerabilities** — 15 known (3 low, 7 moderate, 5 high) in dev deps | 🟡 Medium | Most are in `jsdom`/`vite`/`esbuild` (devDependencies); run `npm audit fix` |
| 13 | **ESLint Next.js plugin** not detected in flat config | 🟢 Low | eslint-config-next doesn't yet support flat config; monitor for upstream fix |

---

## 4. 📊 Performance Matrix (Market-Ready Gates)

### 🎯 Must Pass Before Launch

| Gate | Metric | Target | Measurement Tool |
|------|--------|--------|-----------------|
| P1 | Lighthouse Performance Score | ≥ 90 | `npx lighthouse <url>` |
| P2 | First Contentful Paint (FCP) | < 1.8 s | Lighthouse / PageSpeed Insights |
| P3 | Largest Contentful Paint (LCP) | < 2.5 s | Lighthouse / Core Web Vitals |
| P4 | Cumulative Layout Shift (CLS) | < 0.1 | Lighthouse |
| P5 | Total Blocking Time (TBT) | < 200 ms | Lighthouse |
| P6 | First Load JS per route | < 200 KB | `next build` output |
| P7 | API response time (p95) | < 200 ms | Load test with k6 |
| P8 | Accessibility score | ≥ 90 | Lighthouse Accessibility |
| P9 | No console errors | 0 | Manual / Playwright |
| P10 | Mobile responsive | Pass | Chrome DevTools |

### 🟡 Should Pass Before Scale

| Gate | Metric | Target | Measurement Tool |
|------|--------|--------|-----------------|
| S1 | Time to Interactive (TTI) | < 3.5 s | Lighthouse |
| S2 | Server response time (TTFB) | < 800 ms | Lighthouse |
| S3 | Bundle size (First Load JS shared) | < 80 KB | `next build` output |
| S4 | Redis stream processing latency | < 500 ms | Backend timing logs |
| S5 | Full pipeline latency (signal → DB) | < 3 s | Integration test |
| S6 | Uptime | > 99.5% | UptimeRobot / Vercel |
| S7 | Error rate | < 0.1% | Sentry / Vercel analytics |

---

## 5. 🏁 Launch Checklist

### Infrastructure
- [ ] Set `NEXT_PUBLIC_API_URL` to production backend URL
- [ ] Set `REDIS_URL`, `DATABASE_URL`, `ALLOWED_ORIGINS` in production environment
- [ ] Deploy PostgreSQL (Neon / Railway / Supabase)
- [ ] Deploy Redis (Upstash / Railway)
- [ ] Deploy backend (Railway / Fly.io / EC2)
- [ ] Deploy frontend to Vercel

### Security
- [ ] Add authentication (NextAuth.js or Clerk)
- [ ] Add rate limiting (middleware)
- [ ] Add input validation with Zod on all PATCH endpoints
- [ ] Review CORS `ALLOWED_ORIGINS` — set to production domain only
- [ ] Rotate any credentials that exist in git history
- [ ] Enable Vercel security headers (already in `next.config.ts`)

### Performance
- [ ] Run Lighthouse on production URL — all scores ≥ 90
- [ ] Implement dynamic imports for `/pipeline` and `/demand-miner` routes (reduce 317 KB)
- [ ] Wire `use-leads` to real API (`NEXT_PUBLIC_API_URL/api/leads`)
- [ ] Add `<Suspense>` boundaries around heavy components

### Data / Backend
- [ ] Replace in-memory CRM with real PostgreSQL via SQLAlchemy
- [ ] Add OpenAI API key and wire up AI Analyzer worker
- [ ] Run database migrations (`alembic` or equivalent)
- [ ] Add background job scheduler (APScheduler or Celery) for collector worker

### Monitoring
- [ ] Add Sentry (error tracking)
- [ ] Add Vercel Analytics
- [ ] Add UptimeRobot or similar for uptime monitoring
- [ ] Set up alert thresholds for error rate > 1%

---

## 6. 🧪 Test Coverage Targets

| Layer | Current | Target |
|-------|---------|--------|
| Frontend unit (vitest) | 1 test (example) | ≥ 20 tests |
| Component tests (testing-library) | 0 | ≥ 10 tests |
| API route tests | 0 | ≥ 5 tests |
| Backend unit (pytest) | 0 | ≥ 15 tests |
| E2E (Playwright) | 0 active | ≥ 5 flows |

---

## 7. 📦 Dependency Health

| Package | Version | Issue |
|---------|---------|-------|
| `next` | 15.3.9 | ✅ Patched, no known CVEs |
| `react` | 18.3.1 | ✅ Current stable |
| `vite` | 5.4.19 | ⚠️ Moderate CVE (esbuild dev server) — dev only |
| `jsdom` | 20.0.3 | ⚠️ High CVE (`http-proxy-agent`) — dev/test only |
| `flatted` | — | ⚠️ High CVE — transitive, fix with `npm audit fix` |

> Run `npm audit fix` to auto-fix patchable vulnerabilities in dev deps.

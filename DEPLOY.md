# Lead-iq Production Deployment Checklist (Day 30)

**Last updated:** 2026-05-08

## Pre-Flight (run before deploy)

- [ ] All tests passing: `cd backend && PYTHONPATH=. python -m pytest tests/ -q`
- [ ] Frontend builds: `npm run build`
- [ ] TypeScript types check: `npx tsc --noEmit`
- [ ] Linter passes: `npm run lint`
- [ ] Lighthouse CI scores meet thresholds (perf ≥ 85, a11y ≥ 90, best-practices ≥ 90)
- [ ] No hardcoded secrets: `grep -rn "sk-\|token.*=\|API_KEY.*=" backend/ --include="*.py" | grep -v ".env\|test_"`
- [ ] `.env.example` matches current `.env` keys

## Environment Setup

- [ ] `GEMINI_API_KEY` set and valid (blocker: eval stuck at 12.64% mock without it)
- [ ] `SECRET_KEY` / `JWT_SECRET_KEY` set (min 32 chars, unique per environment)
- [ ] `DATABASE_URL` points to production PostgreSQL (with asyncpg driver)
- [ ] `REDIS_URL` points to production Redis
- [ ] `ALLOWED_ORIGINS` includes production frontend domain
- [ ] `SENTRY_DSN` configured for error tracking
- [ ] All `CLIENT_ID`/`CLIENT_SECRET` pairs verified (Reddit, GitHub, etc.)
- [ ] `MCP_API_KEY` set if MCP endpoint is exposed

## Database

- [ ] All Alembic migrations applied: `cd backend && uv run alembic upgrade head`
- [ ] pgvector extension enabled: `CREATE EXTENSION IF NOT EXISTS vector;`
- [ ] HNSW indexes created for dedup: `CREATE INDEX ON leads USING hnsw (embedding vector_cosine_ops);`
- [ ] Tables present: leads, icps, lead_events, profiles, feedback, quota_usage, lead_dlq

## Services Check

- [ ] Backend health: `GET /api/health` returns 200
- [ ] Redis connected: `GET /api/admin/deploy-check` shows redis=ok
- [ ] Gemini API reachable: `GET /api/admin/deploy-check` shows gemini_api=configured
- [ ] DLQ worker running (Celery Beat `process_dlq_retries` every 5 min)
- [ ] SSE stream healthy: `GET /api/stream/health`
- [ ] Source metrics collecting: `GET /api/admin/source-metrics`

## Security

- [ ] CORS restricted to production origins
- [ ] Rate limiting enabled on all API routes (slowapi)
- [ ] JWT token blocklist active in `services/auth.py`
- [ ] Admin endpoints require valid JWT (`CurrentUser` dependency)
- [ ] Security headers present (HSTS, X-Frame-Options, etc.)
- [ ] No debug mode enabled (`ENVIRONMENT=production`)
- [ ] Secrets rotation log exists (run `python scripts/rotate_secrets.py --audit`)

## Monitoring

- [ ] Sentry configured and receiving events
- [ ] structlog JSON output enabled (`ENVIRONMENT=production`)
- [ ] Axiom/Loki integration configured for structured logs
- [ ] Watchdog health probe returning healthy for all checks
- [ ] Daily metrics persisting to Redis (check `GET /api/admin/daily-metrics`)
- [ ] Lighthouse CI running on main branch pushes

## Performance

- [ ] Bundle analysis reviewed (`ANALYZE=true npm run build`)
- [ ] First Contentful Paint < 2.0s
- [ ] Largest Contentful Paint < 3.5s
- [ ] Total Blocking Time < 300ms
- [ ] Cumulative Layout Shift < 0.1
- [ ] API response time < 600ms (p95)

## Deploy

- [ ] Backend deployed (Railway/GCP)
- [ ] Frontend deployed (Vercel)
- [ ] DNS configured: `app.dreampal.io` → Frontend, `api.dreampal.io` → Backend
- [ ] SSL enabled (automatic with Vercel/Railway)
- [ ] CI/CD passing for main branch (ci.yml + lighthouse.yml)

## Post-Deploy Verification

- [ ] Visit production URL, confirm app loads
- [ ] Login flow works (JWT token received, stored in httpOnly cookie)
- [ ] Navigate all pages (pipeline, demand-miner, command-center, roi-tracker)
- [ ] Run `python eval/run_eval.py` against production backend
- [ ] Check Sentry for errors
- [ ] Check daily metrics endpoint for data
- [ ] Verify SSE stream in browser console

## Rollback Plan

If critical issue found:
1. Revert deploy in Vercel (instant rollback)
2. Revert Railway deploy to previous commit
3. If secrets were rotated, restore previous `.env` values
4. Run smoke tests on rollback
5. Investigate root cause before re-deploying

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Identity

- **Goal:** World's best B2B lead extraction + intelligence platform
- **Stack:** FastAPI (Python 3.11+) + Next.js 15 (App Router) + PostgreSQL + Redis + pgvector + GCP Vertex AI
- **Status:** Production codebase — 17 route modules, 24 collectors, Celery workers, JWT auth, Sentry
- **Repository:** https://github.com/Roshan7869/Lead-iq

## Architecture

```
backend/
  main.py                → FastAPI entrypoint (lifespan: DB + Redis + velocity tracker)
  api/routes/            → 17 route modules: auth, admin, profile, stats, leads, mcp, live_feed,
                            crawler, funding, jobs, government, scoring, outreach, schemes,
                            validate, nlp, ml
  api/deps.py            → FastAPI dependencies (DB session, optional auth)
  api/mcp_server.py      → MCP Streamable HTTP server mounted at /mcp
  models/                → SQLAlchemy ORM: Lead, Post, UserProfile, Feedback, QuotaUsage,
                            GovScheme, FundingEvent, JobSignal, LeadEvent, LeadDLQ, ICP
  shared/
    config.py            → Pydantic BaseSettings singleton — NEVER use os.getenv()
    repository.py        → Repository pattern (PostRepo, LeadRepo, FeedbackRepo, QuotaRepo)
    models.py            → Shared Pydantic models for stream events
    db.py, stream.py     → Async DB engine + Redis stream connection
    logging_config.py    → structlog JSON logger
  services/              → Business logic — NEVER put logic in routes
    auth.py              → JWT auth + token blocklist
    confidence.py        → compute_confidence() — canonical formula (eval-gated)
    dedup_service.py     → 3-tier dedup: exact → fuzzy → pgvector
    icp_service.py       → ICP matching + icp_scorer.py (logistic regression)
    pipeline_service.py  → Lead pipeline state machine
    velocity.py          → Redis-backed velocity tracker
    waterfall_enrichment.py → Multi-source enrichment waterfall
    personalization.py   → Outreach message generation
    intent_monitor.py    → Intent signal detection
    feedback_loop.py     → LeadEvent flywheel (closed-loop feedback)
    temporal_decay.py    → Intent-specific half-lives
    outreach_rag.py      → RAG-based outreach personalization
    rag_{chunker,embedder,indexer,retriever}.py → RAG pipeline
    anomaly_detector.py  → Outlier detection on lead signals
    crawler_orchestrator.py → Multi-source crawler dispatch
    crawlers/            → funding_crawler, govt_schemes_crawler, jobs_crawler
    funding_detector.py  → Funding event detection from news/sources
    job_signals.py       → Job posting signal extraction
    govt_cross_reference.py → Cross-reference govt scheme data
  collectors/            → 24 collectors
    core: github, hn, producthunt, reddit, stackoverflow, twitter, rss, telegram
    govt: dpiit_v2, mca21_v2, government_schemes, msme
    jobs: indeed, internshala, linkedin_jobs, naukri
    other: gem, github_issues, proxy_manager, retry_handler, scraping_utils, scrapling_wrapper, stealth_session
  workers/               → Celery tasks + pipeline stages
    analyzer.py          → 7-stage waterfall analysis (30K — largest file)
    pipeline.py          → End-to-end pipeline orchestration
    scorer.py            → Deterministic lead scoring
    actors.py            → Actor management (GitHub, Telegram, DPIIT, MCA21, Tracxn)
    dlq.py               → Dead Letter Queue worker
    outreach_scorer.py   → Outreach draft quality scoring
    pipeline_stages.py   → Stage-specific processing logic
    source_metrics.py    → Per-source qualification tracking
    rate_limiter.py      → Token budget rate limiter
  llm/                   → Gemini primary (GCP $300 trial)
    gemini_service.py    → extract_lead(), get_embedding() — sole LLM interface
    SOURCE_PROMPTS.py    → 8 source-specific extraction templates (MANDATORY)
    schemas.py           → AnalysisResult Pydantic v2 schema
    cost_guard.py        → Daily (2M) + hourly (83K) token budget enforcement
    circuit_breaker.py   → Prevents cascading failures on API errors
    prompt_versioning.py → A/B test framework for prompt versions
    provider.py          → Abstract LLM provider interface
    ollama_provider.py   → Local Ollama fallback
    heuristic_provider.py → Rule-based fallback (no LLM needed)
    fallback_chain.py    → Provider cascade with fallback logic
  ingestion/             → CLI + orchestrator + metrics + collectors adapter
  engine/                → intent_signals, batch_scorer, scorer
  intelligence/          → signal_fusion, trends
  ml/                    → scoring models: composite_scorer, geo_scorer, rl_scorer,
                            uplift_scorer, scoring_model, feature_engineering
  compliance/            → tos_registry.py (8-source TOS compliance)
  events/                → Redis Stream emitter (emitter.py)
  bot/                   → Telegram bot (formatter, handler, notifier)
  audit/                 → Code audit scripts (council, day1 morning/afternoon)
frontend/                → Next.js 15 App Router, shadcn/ui, Framer Motion, React Query
  src/app/               → /pipeline, /demand-miner, /command-center, /roi-tracker,
                            /funding, /jobs, /schemes, /login
  src/app/api/           → Next.js API routes: health, leads, lead/[id], run-miner,
                            run-ai, mcp, profile, auth
  src/views/             → Overview, DemandMiner, CommandCenter, Pipeline, ROITracker,
                            Funding, JobSignals, Schemes
  src/components/        → AppShell, AppSidebar, LeadCard, StatsCards, profile-setup-wizard
  src/components/ui/     → shadcn/ui primitives (Radix-based)
  src/components/enhanced/ → command-center, lead-card, pipeline-board, stats-cards
  src/hooks/             → use-auth, use-leads, use-profile, use-mobile, use-toast, use-live-feed
  src/lib/               → auth-client.ts, lead-mapper.ts, utils.ts
  src/types/             → lead.ts (Lead, BackendLead, PersonalizedLead, UserProfile, OperationMode)
  src/middleware.ts      → Auth cookie gate + in-memory sliding-window rate limiter
workers/                 → Python actors (Crawlee + Playwright: dpiit, github, mca21, telegram, tracxn)
eval/                    → ground_truth.json + run_eval.py (RUN AFTER EVERY PROMPT CHANGE)
infra/                   → Docker compose (Redis + PostgreSQL + Backend + Frontend)
```

### Event Bus (Redis Streams)

```
lead:collected → lead:analyzed → lead:scored → lead:ranked → lead:outreach → lead:crm_update
system:logs
```

Stream names in `backend/shared/config.py` (`STREAM_COLLECTED`, `STREAM_ANALYZED`, etc.).

## LLM Rules — GEMINI PRIMARY with Fallback Chain

- **BULK EXTRACTION:** `gemini-2.0-flash-lite` ($0.075/M tokens)
- **SCORING/PARSING:** `gemini-2.0-flash` ($0.10/M tokens)
- **EMBEDDINGS:** `text-embedding-004` (pgvector dedup + ICP matching)
- **VISION:** `gemini-2.0-flash` (team pages, images)
- **FALLBACK CHAIN:** Gemini → Ollama (local) → Heuristic (rule-based) — see `llm/fallback_chain.py`
- **NEVER** call Gemini without checking `llm/cost_guard.py` first (daily: 2M tokens, hourly: 83K)
- **DAILY BUDGET:** 2,000,000 tokens max (tracked in Redis key `gemini:tokens:{date}`)
- Extraction uses Vertex AI (`vertexai.generative_models`) with source-grounded prompts, NOT raw JSON parsing

## Source-Specific Prompts (MANDATORY — never use generic prompt)

All prompts in `backend/llm/SOURCE_PROMPTS.py` (`SOURCE_PROMPTS` dict + `get_generic_prompt()`).
Sources: `tracxn` | `indimart` | `github_profile` | `yourstory` | `producthunt` | `hacker_news` | `dpiit` | `mca21`

Each prompt template includes: source context, field extraction instructions, confidence ceiling, and common gotchas.

## Confidence Formula (CANONICAL — never change without running eval)

```python
confidence = compute_confidence(lead_dict, source)  # backend/services/confidence.py
```

SOURCE_TRUST: `github_api=0.95`, `hunter_io=0.90`, `hacker_news=0.82`, `yourstory=0.75`, `producthunt=0.72`, `tracxn=0.70`, `indimart=0.50`, `llm_web_scrape=0.40`

## Dedup Strategy (3-Tier)

All in `backend/services/dedup_service.py`:
1. **Tier 1** — Exact match on email, linkedin_url, company_domain (fast, no cost)
2. **Tier 2** — Fuzzy match via `difflib.SequenceMatcher` on company name, email
3. **Tier 3** — pgvector cosine distance on embeddings (requires `text-embedding-004`)

## Repository Pattern

`backend/shared/repository.py` — all DB queries go here. Workers and routes must NOT touch SQLAlchemy directly.
- `PostRepo` — create / get / exists by hash
- `LeadRepo` — upsert / list / update stage / feedback history
- `FeedbackRepo` — create / list by lead
- `QuotaRepo` — increment / get daily total

Use `selectinload()` to eliminate N+1 queries.

## Frontend Lead Types

`src/types/lead.ts` defines the canonical frontend types:
- `OperationMode`: `'b2b_sales' | 'hiring' | 'job_search' | 'opportunity'` — drives ICP matching
- `LeadStage`: `'detected' | 'qualified' | 'contacted' | 'meeting' | 'closed'`
- `LeadSource`: `'reddit' | 'linkedin' | 'x' | 'yc' | 'indie_hackers' | 'producthunt' | 'stackoverflow' | 'hn' | 'twitter' | 'github' | 'rss'`
- `BackendLead` vs `PersonalizedLead` — the latter adds `personalized_score`, `temporal_decay`, `profile_fit`, etc.

## Database Rules

- ALL DB calls async (asyncpg driver via SQLAlchemy 2.0)
- New models: `id=UUID`, `created_at`, `updated_at` ALWAYS present
- Migration after EVERY schema change:
  ```bash
  cd backend && uv run alembic revision --autogenerate -m "desc"
  ```
- **NEVER** run `alembic upgrade head` without reading the generated file first
- `LeadEvent` table logs EVERY user action (review inbox clicks = training data)
- Use `selectinload()` in repositories to eliminate N+1 queries
- Existing migrations: initial_schema, user_profiles, pgvector_embedding, hnsw_indexes, rag_and_signal_tables

## North Star Metrics (check DAILY before coding)

| Metric | Target |
|--------|--------|
| email_validity_rate | >70% |
| field_precision | >75% vs ground_truth.json eval set |
| gemini_tokens_used | Stay under daily budget |

**RUN:** `python eval/run_eval.py` — if any metric drops, FIX before new features.

See `ROADMAP.md` for current sprint status and session notes.

## Hard Rules (NEVER VIOLATE)

- NEVER commit API keys or secrets — use `.env.local` (frontend) and `.env` (backend)
- NEVER use synchronous DB calls — all SQLAlchemy must be async with `asyncpg`
- NEVER skip Pydantic v2 validation on incoming data
- NEVER call `gemini-pro` for bulk jobs — use `gemini-2.0-flash-lite`
- NEVER run Alembic migrations without reading generated file first
- NEVER change confidence formula without running eval first
- NEVER add a feature if `email_validity_rate < 60%` (quality freeze)
- NEVER use `print()` — use `structlog` logger with structured context
- NEVER use `loop.run_until_complete()` in Celery workers; use `asyncio.run()` or native async
- NEVER use `KEYS` in Redis; use `scan_iter()` to avoid blocking
- NEVER put business logic in route handlers — always delegate to `services/`
- ALWAYS read files before writing code. Say "Reading X" explicitly.
- ALWAYS run `python eval/run_eval.py` after changing any extractor or prompt

## Common Commands

### Backend

```bash
cd backend

# Dependencies (uv)
uv sync --extra dev

# Run dev server
uv run python -m uvicorn backend.main:app --reload --port 8000

# Tests
uv run pytest tests/ -q                          # All tests
uv run pytest tests/ -m integration -q             # Integration tests only
uv run pytest tests/test_file.py::test_func -q   # Single test
RUN_INTEGRATION_TESTS=1 uv run pytest tests/ -q   # Include integration tests (needs Docker)

# Lint / Type Check
uv run ruff check .                                # Lint
uv run ruff check --fix .                          # Auto-fix lint issues
uv run mypy .                                      # Type check
```

### Frontend

```bash
# Install dependencies
npm install

# Dev server (http://localhost:3000)
npm run dev

# Production build
npm run build

# Tests
npm test                           # Run Jest tests
npm run test:watch                 # Watch mode

# Lint & Type Check
npm run lint                       # ESLint
npx tsc --noEmit                   # TypeScript type check

# E2E Tests (Playwright)
npx playwright test                # Run all E2E tests
npx playwright test --ui           # Interactive UI mode
npx playwright test --debug        # Debug mode
```

### Docker (Full Stack)

```bash
cd infra
docker compose up --build          # Start all services (Redis + Postgres + Backend + Frontend)
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Redis: localhost:6379
- PostgreSQL: localhost:5432

### Eval

```bash
python eval/run_eval.py              # Full eval (calls Gemini API)
python eval/run_eval.py --quick      # Cached mode (no API calls, rapid iteration)
python eval/run_eval.py --mock       # Deterministic mock (no Gemini credentials needed)
python eval/run_eval.py --source-list  # List available sources
python eval/run_eval.py --source=tracxn  # Evaluate single source
```

## Environment Variables

See [`.env.example`](.env.example) for full documentation.

### Frontend (`.env.local`)
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Backend API URL |

### Backend (`.env`)
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL asyncpg URL |
| `REDIS_URL` | No | `redis://localhost:6379` | Redis connection |
| `SECRET_KEY` | Yes | — | JWT signing secret |
| `JWT_SECRET_KEY` | Yes | — | JWT secret |
| `ADMIN_USERNAME` | Yes | — | Admin username |
| `ADMIN_PASSWORD` | Yes | — | Admin password |
| `GEMINI_API_KEY` | Optional | — | Gemini API key (Google AI Studio) |
| `GCP_PROJECT_ID` | Optional | — | GCP project for Vertex AI |
| `GITHUB_TOKEN` | Optional | — | GitHub API token |
| `TWITTER_BEARER_TOKEN` | Optional | — | Twitter API token |
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | Optional | — | Reddit API credentials |
| `HUNTER_API_KEY` | Optional | — | Hunter.io email finder |
| `CLEARBIT_API_KEY` | Optional | — | Clearbit company enrichment |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` | Optional | — | Telegram bot + scraping |
| `SENTRY_DSN` | Optional | — | Sentry error tracking |
| `MCP_API_KEY` | Optional | — | Protect /mcp endpoint (empty = no auth) |
| `ALLOWED_ORIGINS` | No | `["http://localhost:3000"]` | CORS origins (JSON array) |

## Deployment

- **Vercel:** `vercel.json` at root — framework: nextjs, builds via `npm run build`
- **Railway:** `railway.toml` at root
- **Docker:** `infra/docker-compose.yml` with separate Dockerfiles for frontend/backend

## Remediation Patterns (Post-Audit 2026-04-25)

### Frontend
- **React Query:** All server state uses `@tanstack/react-query` (`useQuery`, `useMutation`). No raw `fetch` in hooks.
- **Strict TypeScript:** `tsconfig.json` has `strict: true`, `noImplicitAny: true`, `strictNullChecks: true`, `noUnusedLocals: true`, `noUnusedParameters: true`.
- **`ssr: false` in App Router:** `next/dynamic` with `ssr: false` MUST be inside a Client Component (`"use client"`).
- **Error Handling:** Async effects use try/catch/finally; `isMounted` guards prevent state updates after unmount.
- **Middleware:** `src/middleware.ts` handles auth cookie gating (all non-`/login`, non-`/api/auth` paths require `leadiq_session` cookie) + in-memory sliding-window rate limiting on API routes (default: 60 req/min, expensive endpoints: 10 req/min).

### Backend
- **Auth:** Token blocklist in `services/auth.py` (`_token_blocklist: set[str]`). `verify_token()` checks blocklist for refresh tokens.
- **Config:** `shared/config.py` — `Settings` class with `case_sensitive = True`. Module-level `settings = Settings()` singleton.
- **Error Handling:** Raise specific exceptions (`GeminiExtractionError`) instead of returning error dicts.
- **Rate Limiting:** `slowapi` limiter attached to `app.state.limiter` in `main.py` (default: 120/min, auth: 10/min, expensive: 5/min).

### Testing
- `conftest.py` adds project root to `sys.path` and sets dummy env vars (`SECRET_KEY`, `DATABASE_URL`, etc.) so `Settings()` instantiates during collection.
- Integration tests require Docker-backed Postgres/Redis; set `RUN_INTEGRATION_TESTS=1` to enable.
- Test directories mirror source: `tests/services/`, `tests/collectors/`, `tests/ml/`, `tests/architecture/`, `tests/fixtures/`.

### Session Protocol
1. **READ** `ROADMAP.md` completely at session start
2. **IDENTIFY** which task is In Progress
3. **SWITCH** to Plan Mode for complex tasks
4. **EXECUTE** only the approved next step
5. **VERIFY** and update `ROADMAP.md` after completion

## gstack (recommended)

This project uses [gstack](https://github.com/garrytan/gstack) for AI-assisted workflows.
Install it for the best experience:

```bash
git clone --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
cd ~/.claude/skills/gstack && ./setup --team
```

Skills like /qa, /ship, /review, /investigate, and /browse become available after install.
Use /browse for all web browsing. Use ~/.claude/skills/gstack/... for gstack file paths.

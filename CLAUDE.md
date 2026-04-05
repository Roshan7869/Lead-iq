# Lead-iq — AI B2B Lead Intelligence Platform
# READ THIS COMPLETELY BEFORE WRITING ANY CODE

## Identity
- Goal: World's best lead extraction + intelligence (10 years ahead of Apollo/ZoomInfo)
- Stack: FastAPI (Python 3.12) + Next.js 15 + PostgreSQL + Redis + pgvector + GCP Vertex AI
- Status: Production codebase — 15+ endpoints, 7 collectors, Celery workers, JWT auth, Sentry
- Repository: https://github.com/Roshan7869/Lead-iq

## Architecture
```
backend/
  routes/       → auth, admin, profile, stats, leads, collectors
  models/       → SQLAlchemy ORM (async, UUID PKs, created_at/updated_at on all)
  services/     → business logic — NEVER put logic in routes
  collectors/   → github, hn, producthunt, reddit, stackoverflow, twitter, rss
  workers/      → Celery tasks (all async)
  llm/          → gemini_service.py (ONLY LLM layer — see rules)
  services/     → dedup_service.py, confidence.py, intent_monitor.py, icp_service.py
  graph/        → queries.py (pgvector + future Neo4j)
frontend/       → Next.js 15, shadcn/ui, Framer Motion, React Query
workers/        → Python actors (Crawlee + Playwright, separate from backend/)
eval/           → ground_truth.json + run_eval.py (RUN AFTER EVERY PROMPT CHANGE)
```

## LLM Rules — GEMINI ONLY (GCP $300 trial)
- BULK EXTRACTION:  gemini-2.0-flash-lite  ($0.075/M tokens)
- SCORING/PARSING:  gemini-2.0-flash       ($0.10/M tokens)
- EMBEDDINGS:       text-embedding-004     (pgvector dedup + ICP matching)
- VISION:           gemini-2.0-flash       (team pages, images)
- NEVER call Gemini without checking backend/llm/cost_guard.py first
- DAILY BUDGET: 2,000,000 tokens max (tracked in Redis key gemini:tokens:{date})
- USE LangExtract library — NOT raw prompt JSON parsing

## Source-Specific Prompts (MANDATORY — never use generic prompt)
All prompts are in backend/llm/SOURCE_PROMPTS dict in gemini_service.py
Sources: tracxn | indimart | github_profile | yourstory | producthunt | hacker_news | dpiit | mca21

## Confidence Formula (CANONICAL — never change without updating eval)
confidence = compute_confidence(lead_dict, source) in backend/services/confidence.py
SOURCE_TRUST: github_api=0.95, hunter_io=0.90, hacker_news=0.82,
              yourstory=0.75, producthunt=0.72, tracxn=0.70,
              indimart=0.50, llm_web_scrape=0.40

## Database Rules
- ALL DB calls async (asyncpg driver)
- New models: id=UUID, created_at, updated_at ALWAYS present
- Migration after EVERY schema change: alembic revision --autogenerate -m "desc"
- NEVER run alembic upgrade head without reading the generated file first
- LeadEvent table logs EVERY user action (review inbox clicks = training data)

## North Star Metrics (check DAILY before coding)
- email_validity_rate  → target: >70%
- field_precision      → target: >75% vs ground_truth.json eval set
- gemini_tokens_used   → must stay under daily budget
RUN: `python eval/run_eval.py` — if any metric drops, FIX before new features

## Current Sprint (Days 0–12)
Day 0:  COMPLETE? [ ] eval/ground_truth.json + cost_guard.py + LeadEvent model
Day 1:  COMPLETE? [ ] LangExtract + SOURCE_PROMPTS all sources
Day 2:  COMPLETE? [ ] baseline eval score — record in TODO.md
Day 3:  COMPLETE? [ ] pgvector embedding column + dedup_service.py
Day 4:  COMPLETE? [ ] confidence.py + SOURCE_TRUST + Celery dedup task
Day 5:  COMPLETE? [ ] DPIIT actor (free government API)
Day 6:  COMPLETE? [ ] Tracxn actor + MCA21 actor
Day 7:  COMPLETE? [ ] temporal decay + intent_monitor.py (30-min Celery beat)
Day 8:  COMPLETE? [ ] waterfall enrichment with Redis quota guards
Day 9:  COMPLETE? [ ] ICP NLP parser (Gemini Flash)
Day 10: COMPLETE? [ ] pgvector ICP matching + deterministic scoring
Day 11: COMPLETE? [ ] Next.js live feed + review inbox + LeadEvent logging
Day 12: COMPLETE? [ ] daily metrics task + MCP server endpoint + deploy-check

## Hard Rules (NEVER VIOLATE)
- NEVER commit API keys or secrets — use `.env.local` (frontend) and `.env` (backend)
- NEVER use synchronous DB calls — all SQLAlchemy must be async with `asyncpg`
- NEVER skip Pydantic v2 validation on incoming data
- NEVER call gemini-pro for bulk jobs — use gemini-2.0-flash-lite
- NEVER run Alembic migrations without reading generated file first
- NEVER change confidence formula without running eval first
- NEVER add a feature if email_validity_rate < 60% (quality freeze)
- NEVER use `print()` — use `structlog` logger with structured context
- ALWAYS read files before writing code. Say "Reading X" explicitly.
- ALWAYS run: `python eval/run_eval.py` after changing any extractor or prompt

## Common Commands

### Backend
```bash
cd backend
uv sync --extra dev                    # Install dependencies (uv)
uv run pytest backend/tests -q         # Run unit tests
uv run pytest backend/tests -m integration  # Run integration tests
uv run alembic revision --autogenerate -m "desc"  # Create migration
uv run alembic upgrade head            # Apply migrations
uv run python -m uvicorn main:app --reload  # Run dev server
```

### Frontend
```bash
npm install                            # Install dependencies
npm run dev                            # Run dev server (http://localhost:3000)
npm run build                          # Production build
npm test                               # Run Jest tests
npm run lint                           # Run ESLint
```

### Docker
```bash
cd infra
docker compose up --build              # Start all services
```

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.

## Environment Variables

See [`.env.example`](.env.example) for full documentation.

### Frontend (`.env.local`)
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Backend API URL |

### Backend (`.env`)
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | No | `redis://localhost:6379` | Redis connection |
| `DATABASE_URL` | Yes | — | PostgreSQL asyncpg URL |
| `ALLOWED_ORIGINS` | No | `["http://localhost:3000"]` | CORS origins |
| `DEBUG` | No | `False` | Debug mode |
| `GEMINI_API_KEY` | Optional | — | Gemini API key (Google AI Studio) |
| `GCP_PROJECT_ID` | Optional | — | GCP project for Vertex AI |
| `SECRET_KEY` | Yes | — | JWT signing secret |
| `JWT_SECRET_KEY` | Yes | — | JWT secret |
| `ADMIN_PASSWORD` | Yes | — | Admin password |
| `REDDIT_CLIENT_ID` | Optional | — | Reddit API credentials |
| `REDDIT_CLIENT_SECRET` | Optional | — | Reddit API credentials |
| `TWITTER_BEARER_TOKEN` | Optional | — | Twitter API token |
| `GITHUB_TOKEN` | Optional | — | GitHub API token |

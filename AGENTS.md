# AGENTS.md — LeadIQ

## MCP Tools (use first)

This project has a **code-review-graph** MCP server (configured in `.opencode.json` and `.mcp.json`). Always use graph tools before Grep/Glob/Read — they're faster and give structural context (callers, dependents, test coverage).

| Tool | Use when |
|------|----------|
| `semantic_search_nodes` | Finding functions/classes by name |
| `query_graph` | Tracing callers, callees, imports, tests |
| `get_impact_radius` | Blast radius of a change |
| `get_affected_flows` | Which execution paths are impacted |
| `get_architecture_overview` | High-level codebase structure |

Also available: **NEXUS v3** routing at `/home/roshan/nexus/` (`tool_attention_route`, `universal_route`, `find_skills`).

## Reference doc

**CLAUDE.md** at root is the canonical reference (architecture, all commands, env vars, hard rules). Read it at session start. This file only covers what's non-obvious.

## Two-package split

| Layer | PM | Dir | Test cmd |
|-------|----|-----|----------|
| **Frontend** (Next.js 15) | npm | root `src/` | `npm test` (Jest, jsdom) |
| **Backend** (FastAPI) | uv | `backend/` | `uv run pytest backend/tests -q` |

Frontend tests live under `src/**/*.test.{ts,tsx}`. Backend tests mirror source structure under `backend/tests/`.

## Commands agents guess wrong

- **Type check frontend**: `npx tsc --noEmit` (not just `npm run lint`)
- **Run single backend test**: `uv run pytest backend/tests/test_file.py::test_func -q -m 'not integration'`
- **Run single frontend test**: `npm test -- --testPathPattern=MyComponent`
- **Integration tests**: need Docker-backed Postgres+Redis; set `RUN_INTEGRATION_TESTS=1`
- **Lint → typecheck → test** order matters in CI (see `.github/workflows/ci.yml`)
- **Eval**: Always run `python eval/run_eval.py` after changing any LLM prompt or extractor. Has `--quick` (cached) and `--mock` (no API key) modes.

## Pre-commit hooks (`.pre-commit-config.yaml`)

Run automatically on commit. They execute:
1. `ruff --fix` + `ruff-format` (backend Python)
2. `end-of-file-fixer`, `trailing-whitespace`, `check-merge-conflict`, `check-yaml`
3. `npm test -- --runInBand` (all frontend Jest tests)
4. `uv run --project backend pytest backend/tests -q` (all backend tests)

This means **all tests must pass before any commit**. Fix issues before attempting to commit, or the hook will reject.

## Backend patterns (non-obvious)

- **Config**: `backend/shared/config.py` — `Settings()` singleton via `pydantic-settings`. **Never** use `os.getenv()`.
- **Business logic** must go in `backend/services/`, never in route handlers.
- **DB queries** go through `backend/shared/repository.py` (Repository pattern) — never direct SQLAlchemy in routes/workers.
- **LLM**: Gemini primary via Vertex AI (`backend/llm/gemini_service.py`). Always check `cost_guard.py` before calling. Fallback chain: Gemini → Ollama → Heuristic.
- **Source prompts**: `backend/llm/SOURCE_PROMPTS.py` — mandatory source-grounded prompts per extraction source. Never use a generic prompt.
- **Confidence formula**: `backend/services/confidence.py` — canonical, eval-gated.
- **Dedup**: 3-tier (exact → fuzzy → pgvector) in `backend/services/dedup_service.py`.

## Deployment

- **Frontend**: Vercel (`vercel.json`, `npm run build`)
- **Backend**: Railway (`railway.toml`, Docker images via `infra/Dockerfile.backend`)
- **Full stack locally**: `cd infra && docker compose up --build`

## Style quirks

- **ESLint** has `no-unused-vars`, `no-explicit-any`, `no-empty-object-type` all **off** — don't flag these.
- **TypeScript** is strict: `strict: true`, `noUnusedLocals: true`, `noUnusedParameters: true`.
- **Backend mypy** is non-strict (`ignore_missing_imports = true`).
- Ruff line length: 100; target py311.
- Next.js middleware (`src/middleware.ts`): auth cookie gating + in-memory rate limiting (60 req/min default, 10 req/min for expensive endpoints).
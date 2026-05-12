# Autopilot Execution Plan
> GStack + NEXUS Adaptive-Imagining-Cat Execution DAG
> Fix all 33 gaps in 7 sprints with verification/audit gates
> Date: 2026-05-12

---

## Architecture: GStack + NEXUS Hybrid

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTOPILOT ORCHESTRATOR                     │
│  (NEXUS adaptive-imagining-cat DAG + GStack team roles)      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Phase Gates:  RESEARCH → DESIGN → IMPLEMENT → TEST → DEPLOY │
│                    ↕ verification        ↕ audit              │
│                                                               │
│  GStack Roles:                                                │
│  ├── /autoplan    → CEO review of each sprint plan           │
│  ├── /review      → PR review at every gate                  │
│  ├── /qa          → Browser QA for collector platforms       │
│  ├── /cso         → Security audit at deployment gate        │
│  ├── /ship        → Ship workflow per sprint                 │
│  ├── /canary      → Post-deploy monitoring                   │
│  ├── /benchmark   → Performance regression detection         │
│  └── /retro       → Retrospective after each phase           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Sprint Structure (7 Sprints × Verification Gate + Audit Gate)

Each sprint follows: PLAN → GATE(verify) → BUILD → GATE(test) → SHIP → GATE(audit)

```
SPRINT [N]
  ├── /autoplan        → CEO reviews plan against requirements
  ├── IMPLEMENT        → Code + tests (TDD)
  ├── VERIFICATION GATE → All tests pass, no regressions
  │     ├── pytest tests/ -q                    # Backend tests
  │     ├── npm test                            # Frontend tests
  │     └── python eval/run_eval.py --mock      # Eval regression check
  ├── /review          → PR review gate
  ├── /qa              → QA verification (if applicable)
  └── AUDIT GATE       → Compare actual vs planned
        ├── Count deliverables completed
        ├── Log blockers discovered
        └── /retro      → Learnings for next sprint
```

---

## SPRINT 1: Blockers + Tech Debt

**Goal:** Get test suite to 100% pass, unblock eval pipeline
**Duration:** 3 days
**GStack Roles:** /autoplan, /review, /ship

### Tasks

| # | Task | File(s) | Verification |
|---|------|---------|-------------|
| 1.1 | Add GEMINI_API_KEY to .env | `.env` | `python eval/run_eval.py` returns real precision |
| 1.2 | Add NVIDIA_API_KEY to .env | `.env` | Key loads without error in llm_router.py |
| 1.3 | Fix Pydantic v2 class Config | `shared/config.py:13`, `api/schemas.py` | No DeprecationWarning |
| 1.4 | Add missing deps to pyproject.toml | `backend/pyproject.toml` | `uv sync` installs all |
| 1.5 | Fix SQLAlchemy model ordering | `models/lead_event.py` | DLQ tests pass |
| 1.6 | Add fetch polyfill for Jest | `src/test/setup.ts` | Frontend tests pass |
| 1.7 | Re-run full test suite | — | 100% pass rate |

### Verification Gate (S1-V)

```bash
cd backend && uv run pytest tests/ -q -m "not integration"    # All backend tests pass
cd backend && uv run ruff check .                              # No lint errors
cd backend && uv run mypy .                                    # Type check passes
cd frontend && npm test                                        # All frontend tests pass
python eval/run_eval.py --mock                                 # Eval runs clean
```

### Audit Gate (S1-A)

- [ ] Test suite pass rate: ___ / ___ (target: 100%)
- [ ] Eval precision: ___ % (target: real >12.64%)
- [ ] New blockers discovered: ___
- [ ] /retro learnings logged to `plans/retro/`

---

## SPRINT 2: High-Value Job Collectors

**Goal:** Deploy LinkedIn Jobs + Indeed collectors
**Duration:** 4 days
**GStack Roles:** /autoplan, /review, /qa, /ship
**Research Basis:** Scrapus (Frontiers 2025) — API interception + DOM traversal

### Tasks

| # | Task | File(s) | Pattern |
|---|------|---------|---------|
| 2.1 | LinkedIn Jobs collector | `collectors/linkedin_jobs.py` | StealthSession + GraphQL API intercept (see naukri.py) |
| 2.2 | Register /api/jobs/collect/linkedin | `api/routes/jobs.py` | POST route |
| 2.3 | Add to JobsCrawler | `services/crawlers/jobs_crawler.py` | Add to crawler dispatch |
| 2.4 | LinkedIn compliance entry | `compliance/tos_registry.py` | ToS check |
| 2.5 | Indeed collector | `collectors/indeed.py` | API interception + HTML fallback |
| 2.6 | Register /api/jobs/collect/indeed | `api/routes/jobs.py` | POST route |
| 2.7 | Indeed compliance entry | `compliance/tos_registry.py` | ToS check |

### Verification Gate (S2-V)

```bash
cd backend && uv run pytest tests/ -q -m "not integration"    # No regressions
# Manual smoke test:
curl -X POST http://localhost:8000/api/jobs/collect/linkedin
curl -X POST http://localhost:8000/api/jobs/collect/indeed
python -c "from backend.collectors import linkedin_jobs; c=linkedin_jobs.LinkedInJobsCollector(); print(c.collect(keywords=['software-engineer'], location='bangalore'))"
```

### Audit Gate (S2-A)

- [ ] LinkedIn: ___ jobs extracted (target: 50+ in smoke test)
- [ ] Indeed: ___ jobs extracted (target: 50+ in smoke test)
- [ ] No IP blocks observed
- [ ] Test pass rate: 100%
- [ ] /retro learnings logged

---

## SPRINT 3: Actor Workers

**Goal:** Create standalone Crawlee actors for Naukri + Internshala
**Duration:** 3 days
**GStack Roles:** /autoplan, /review, /ship
**Research Basis:** asLLR (arXiv 2510.21713) — LLM enrichment after raw collection

### Tasks

| # | Task | File(s) | Pattern |
|---|------|---------|---------|
| 3.1 | Naukri actor worker | `workers/naukri-actor/main.py` | Follow github-actor pattern (Crawlee PlaywrightCrawler) |
| 3.2 | Naukri actor Dockerfile | `workers/naukri-actor/Dockerfile` | Follow greptor-actor pattern |
| 3.3 | Naukri actor requirements.txt | `workers/naukri-actor/requirements.txt` | Crawlee + Playwright |
| 3.4 | Internshala actor worker | `workers/internshala-actor/main.py` | HTTP-based (no Playwright needed) |
| 3.5 | Internshala actor Dockerfile | `workers/internshala-actor/Dockerfile` | Python HTTP |
| 3.6 | Wire actors into pipeline | `workers/pipeline.py` | Register new actor types |
| 3.7 | Add Redis stream routing | `events/emitter.py` | Route actor output to lead:collected |

### Verification Gate (S3-V)

```bash
cd workers/naukri-actor && python main.py --dry-run           # Test extraction
cd workers/internshala-actor && python main.py --dry-run      # Test extraction
cd backend && uv run pytest tests/ -q -m "not integration"    # No regressions
```

### Audit Gate (S3-A)

- [ ] Naukri actor: ___ jobs extracted per run
- [ ] Internshala actor: ___ internships extracted per run
- [ ] Pipeline registration complete
- [ ] Test pass rate: 100%
- [ ] /retro learnings logged

---

## SPRINT 4: Government API + Shine

**Goal:** API Setu integration + Shine.com collector
**Duration:** 3 days
**GStack Roles:** /autoplan, /review, /qa, /ship
**Research Basis:** CPOG (LinkedIn 2025) — DAG-based pipeline integration

### Tasks

| # | Task | File(s) | Pattern |
|---|------|---------|---------|
| 4.1 | API Setu client | `collectors/apisetu_client.py` | HTTPS API client |
| 4.2 | API Setu route | `api/routes/govt.py` | GET /api/govt/apisetu/search |
| 4.3 | Cross-reference integration | `services/govt_cross_reference.py` | Link MCA21 + GST + Udyam |
| 4.4 | Shine.com collector | `collectors/shine.py` | HTTP + BeautifulSoup (see internshala.py) |
| 4.5 | Shine route | `api/routes/jobs.py` | POST /api/jobs/collect/shine |
| 4.6 | Shine compliance entry | `compliance/tos_registry.py` | ToS check |

### Verification Gate (S4-V)

```bash
curl http://localhost:8000/api/govt/apisetu/search?q=test
curl -X POST http://localhost:8000/api/jobs/collect/shine
cd backend && uv run pytest tests/ -q -m "not integration"
```

### Audit Gate (S4-A)

- [ ] API Setu: ___ records retrieved
- [ ] Shine: ___ jobs extracted
- [ ] Cross-reference pipeline operational
- [ ] Test pass rate: 100%
- [ ] /retro learnings logged

---

## SPRINT 5: Infrastructure Hardening

**Goal:** stream_v2.py + full test pyramid (integration, load, E2E)
**Duration:** 4 days
**GStack Roles:** /autoplan, /review, /qa, /benchmark, /ship
**Research Basis:** CPOG (LinkedIn 2025) — production stream architecture

### Tasks

| # | Task | File(s) | Description |
|---|------|---------|-------------|
| 5.1 | stream_v2.py — enhanced streams | `shared/stream_v2.py` | Multi-source routing, per-stream DLQ, checkpoint tracking, backpressure |
| 5.2 | Integration tests — pipeline | `tests/integration/test_pipeline.py` | Collector → stream → analyzer → scorer → persist |
| 5.3 | Integration tests — API endpoints | `tests/integration/test_api_endpoints.py` | All 17 route modules E2E |
| 5.4 | Integration tests — Redis streams | `tests/integration/test_redis_streams.py` | Stream publish/consume with real Redis |
| 5.5 | Load tests — collection rate | `tests/load/test_collection_rate.py` | Collector throughput under load |
| 5.6 | Load tests — API throughput | `tests/load/test_api_throughput.py` | API response time at 100 req/s |
| 5.7 | Load tests — pipeline capacity | `tests/load/test_pipeline_capacity.py` | 25K leads/day throughput |
| 5.8 | E2E tests — full flow | `tests/e2e/test_full_flow.py` | Frontend → API → Backend → DB → Display |
| 5.9 | E2E tests — production scenarios | `tests/e2e/test_production_scenarios.py` | Login → Mine → Score → Outreach |

### Verification Gate (S5-V)

```bash
RUN_INTEGRATION_TESTS=1 cd backend && uv run pytest tests/integration/ -q
cd backend && uv run pytest tests/load/ -q
cd frontend && npx playwright test tests/e2e/
cd backend && uv run pytest tests/ -q                              # All tests pass
```

### Audit Gate (S5-A)

- [ ] Integration tests: ___ / ___ pass
- [ ] Load tests: collection rate ___ jobs/min (target: scalable)
- [ ] E2E tests: ___ / ___ pass
- [ ] Test coverage: ___ % (target: >80%)
- [ ] /retro learnings logged

---

## SPRINT 6: Niche Platforms (Batch)

**Goal:** 14 remaining platform collectors — HTTP + BeautifulSoup pattern
**Duration:** 4 days
**GStack Roles:** /autoplan, /review, /ship
**Research Basis:** Scrapus (Frontiers 2025) — parallelization across sources

### Tasks (Mass-Producible — ~2 hours each)

| # | Platform | Tier | Collector File | Route |
|---|----------|------|---------------|-------|
| 6.1 | Monster India | T2 | `collectors/monster.py` | /api/jobs/collect/monster |
| 6.2 | NaukriGulf | T2 | `collectors/naukrigulf.py` | /api/jobs/collect/naukrigulf |
| 6.3 | Freshersworld | T3 | `collectors/freshersworld.py` | /api/jobs/collect/freshersworld |
| 6.4 | Hirist | T3 | `collectors/hirist.py` | /api/jobs/collect/hirist |
| 6.5 | CutShort | T3 | `collectors/cutshort.py` | /api/jobs/collect/cutshort |
| 6.6 | Instahyre | T3 | `collectors/instahyre.py` | /api/jobs/collect/instahyre |
| 6.7 | Hirect | T3 | `collectors/hirect.py` | /api/jobs/collect/hirect |
| 6.8 | Weekday | T3 | `collectors/weekday.py` | /api/jobs/collect/weekday |
| 6.9 | TimesJobs | T3 | `collectors/timesjobs.py` | /api/jobs/collect/timesjobs |
| 6.10 | Foundit (Monster) | T3 | `collectors/foundit.py` | /api/jobs/collect/foundit |
| 6.11 | Sarkari Result | T5 | `collectors/sarkari_result.py` | /api/jobs/collect/sarkari |
| 6.12 | FreeJobAlert | T5 | `collectors/freejobalert.py` | /api/jobs/collect/freejobalert |
| 6.13 | Employment News | T5 | `collectors/employment_news.py` | /api/jobs/collect/employment |
| 6.14 | iimjobs | T3 | `collectors/iimjobs.py` | /api/jobs/collect/iimjobs |

Each collector follows the contract:
```python
class PlatformCollector(BaseCollector):
    async def collect(self, keywords: List[str], **kwargs) -> List[RawPost]: ...
    def transform(self, raw: RawPost) -> Lead: ...
```

### Verification Gate (S6-V)

```bash
# Mass smoke test:
for platform in monster naukrigulf freshersworld hirist cutshort instahyre hirect weekday timesjobs foundit sarkari freejobalert employment iimjobs; do
  curl -X POST "http://localhost:8000/api/jobs/collect/$platform" -H "Content-Type: application/json" -d '{"keywords":["software-engineer"],"location":"bangalore"}' &
done
wait
cd backend && uv run pytest tests/ -q
```

### Audit Gate (S6-A)

- [ ] Platforms implemented: ___ / 14
- [ ] Total new leads/day potential: ___
- [ ] Test pass rate: 100%
- [ ] No regressions in existing collectors
- [ ] /retro learnings logged

---

## SPRINT 7: Deployment + Verification

**Goal:** Production deployment, eval gate, monitoring
**Duration:** 3 days
**GStack Roles:** /autoplan, /cso, /canary, /benchmark, /ship

### Tasks

| # | Task | Description | Verification |
|---|------|-------------|-------------|
| 7.1 | Set production API keys | GEMINI_API_KEY + NVIDIA_API_KEY in Railway/Vercel | `python eval/run_eval.py` >75% precision |
| 7.2 | Run Alembic migrations | Any schema changes from new collectors | Migration applies cleanly |
| 7.3 | Deploy backend to Railway | `railway up` | /api/health returns 200 |
| 7.4 | Deploy frontend to Vercel | `vercel --prod` | App loads in browser |
| 7.5 | Verify all endpoints | `curl https://api.leadiq.app/api/health` | All 17 route modules respond |
| 7.6 | Full eval run | `python eval/run_eval.py` | Field precision >75%, email_validity >70% |
| 7.7 | Lighthouse CI | `npx lighthouse-ci https://app.leadiq.app` | Performance >90, Accessibility >90 |
| 7.8 | /cso security audit | Full OWASP Top 10 + STRIDE | No CRITICAL/HIGH findings |
| 7.9 | /canary monitoring | Post-deploy watch for 24h | No error spikes |

### Verification Gate (S7-V)

```bash
curl https://api.leadiq.app/api/health                           # 200 OK
curl https://api.leadiq.app/api/stats                            # Returns metrics
python eval/run_eval.py                                           # >75% field precision
cd backend && uv run pytest tests/ -q                            # 100% pass
npx lighthouse-ci https://app.leadiq.app                          # >90 all categories
```

### Audit Gate (S7-A) — FINAL

- [ ] All 33 gaps resolved
- [ ] Test suite: 100% pass rate
- [ ] Eval field precision: ___ % (target: >75%)
- [ ] Eval email_validity_rate: ___ % (target: >70%)
- [ ] Daily lead capacity: ___ (target: 25K+)
- [ ] Security audit: ___ findings (target: 0 CRITICAL)
- [ ] Lighthouse: Perf ___ / Access ___ / BestPrac ___ / SEO ___
- [ ] /retro learnings logged

---

## Global Verification & Audit Gates

### VERIFICATION GATE PROTOCOL

Every gate requires ALL of these before proceeding:

```
┌─ VERIFICATION CHECKLIST ─────────────────────┐
│ ✅ All backend tests pass                     │
│   → cd backend && uv run pytest tests/ -q     │
│ ✅ All frontend tests pass                    │
│   → cd frontend && npm test                   │
│ ✅ Eval runs without error                    │
│   → python eval/run_eval.py --mock            │
│ ✅ No lint errors                             │
│   → cd backend && uv run ruff check .         │
│ ✅ Type check passes                          │
│   → cd backend && uv run mypy .               │
│ ✅ No regression in existing collectors       │
│   → curl smoke test on existing endpoints     │
│ ───────────────────────────────────────────── │
│ FAIL → Stop. Fix before proceeding.           │
└──────────────────────────────────────────────┘
```

### AUDIT GATE PROTOCOL

Every gate produces a written audit:

```
┌─ AUDIT CHECKLIST ────────────────────────────┐
│ 📊 Deliverables: Planned ___ / Actual ___     │
│ 📊 Test pass rate: ___ %                      │
│ 📊 Eval precision delta: ___ %                │
│ 🐛 New blockers discovered: ___               │
│ 📝 Learnings (/retro):                        │
│   1. ...                                      │
│   2. ...                                      │
│ ───────────────────────────────────────────── │
│ PASS → Proceed to next sprint                 │
│ FAIL → /retro → Fix issues → Re-verify        │
└──────────────────────────────────────────────┘
```

---

## DAG Execution Flow

```
                        ┌──────────────────┐
                        │   NEXUS Plan #8   │
                        │ (adaptive-imagining│
                        │    -cat workflow)  │
                        └────────┬─────────┘
                                 │
                  ┌──────────────┼──────────────┐
                  ▼              ▼              ▼
          ┌────────────┐ ┌────────────┐ ┌────────────┐
          │  Phase 1   │ │  Phase 2   │ │  Phase 3   │
          │  Research  │ │  Design    │ │  Implement │
          └──────┬─────┘ └──────┬─────┘ └──────┬─────┘
                 │              │              │
                 └──────────────┼──────────────┘
                                ▼
                        ┌──────────────┐
                        │  VERIFY GATE  │ ← NEXUS verify_phase()
                        │  + GStack     │
                        │  /review      │
                        └──────┬───────┘
                               ▼
                        ┌──────────────┐
                        │  Phase 3.5   │
                        │  Test + QA   │ ← GStack /qa
                        └──────┬───────┘
                               ▼
                        ┌──────────────┐
                        │  AUDIT GATE   │ ← GStack /retro
                        └──────┬───────┘
                               ▼
                        ┌──────────────┐
                        │  Phase 4     │
                        │  Deploy      │ ← GStack /ship + /canary
                        └──────┬───────┘
                               ▼
                        ┌──────────────┐
                        │  Phase 5     │
                        │  Verify Plan │ ← NEXUS verify_phase()
                        └──────┬───────┘
                               ▼
                        ┌──────────────┐
                        │  Phase 6     │
                        │  Audit       │ ← NEXUS audit_plan()
                        │  + GStack    │
                        │  /retro      │
                        └──────────────┘
```

## Execution Commands

### Start a sprint from NEXUS:

```bash
# Execute a phase of plan #8
mcp__nexus__execute_phase(plan_id=8, phase_id="phase-3-implement")

# Verify phase output before proceeding
mcp__nexus__verify_phase(plan_id=8, phase_id="phase-3-implement")

# Run audit on completed plan
mcp__nexus__audit_plan(plan_id=8)
```

### Run GStack gates:

```bash
# CEO review of sprint plan
/gstack /autoplan "Sprint N: <description>"

# Code review gate
/gstack /review

# QA gate (for collector sprints)
/gstack /qa

# Security audit (Sprint 7)
/gstack /cso

# Ship workflow
/gstack /ship

# Retrospective
/gstack /retro "Sprint N: <summary>"
```

### Health checks during execution:

```bash
# NEXUS system health
mcp__nexus__nexus_health()

# Routing health
mcp__nexus__audit_routing()
```

---

## Success Criteria (Final Gate)

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Test pass rate | 30/36 backend, 4/5 frontend | 100% all suites | `pytest tests/ -q` + `npm test` |
| Eval field precision | 12.64% (mock) | >75% | `python eval/run_eval.py` |
| Eval email_validity_rate | Unknown (no API key) | >70% | `python eval/run_eval.py` |
| Platforms implemented | 10/29 | 29/29 | `plans/platforms/PLATFORM_CATALOG.md` |
| Daily lead capacity | ~500 | 25,000+ | Pipeline throughput measurement |
| Test coverage | Unknown | >80% | `pytest --cov` |
| Lighthouse score | Unknown | >90 all | `lighthouse-ci` |
| Security audit | Unknown | 0 CRITICAL | `/cso` report |

---

*Autopilot Execution Plan v1.0*
*Engine: NEXUS adaptive-imagining-cat + GStack team roles*
*Total: 7 sprints, 24 days, 33 gaps, 6 verification gates, 7 audit gates*

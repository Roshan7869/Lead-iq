---
type: architecture
name: GitNexus Stack Analysis
layers: 7
created: 2026-04-25
---

# GitNexus Stack — Code-Review-Graph Based Remediation Architecture

> "The GitNexus is the structural memory of the codebase. The Stack is how we remediate it layer by layer."

## Overview

The GitNexus Stack uses the `.code-review-graph/graph.db` as the source of truth for all remediation decisions. Instead of treating fixes as isolated changes, we map them to the **7 layers of the stack**, each with its own blast radius, dependency graph, and verification protocol.

## The 7 Layers

```
┌─────────────────────────────────────────────┐
│  LAYER 7: Telemetry & Observability         │  ← Metrics, eval, dashboards
│  (eval/, admin routes, daily_report)        │
├─────────────────────────────────────────────┤
│  LAYER 6: Pipeline & Workers                 │  ← Celery, Redis Streams, DLQ
│  (workers/pipeline.py, workers/actors.py)   │
├─────────────────────────────────────────────┤
│  LAYER 5: LLM Intelligence Layer             │  ← Gemini, prompts, embeddings
│  (backend/llm/*, services/icp_service.py)   │
├─────────────────────────────────────────────┤
│  LAYER 4: Business Logic & Services          │  ← Confidence, dedup, enrichment
│  (services/confidence.py, dedup_service.py)   │
├─────────────────────────────────────────────┤
│  LAYER 3: Data Access Layer                  │  ← Repositories, models, migrations
│  (shared/repository.py, shared/models.py)    │
├─────────────────────────────────────────────┤
│  LAYER 2: API Gateway & Auth                 │  ← Routes, deps, JWT, rate limiting
│  (api/routes/*, api/deps.py, services/auth)  │
├─────────────────────────────────────────────┤
│  LAYER 1: Infrastructure & Config          │  ← DB, Redis, Celery, Docker
│  (shared/db.py, shared/config.py, infra/)    │
└─────────────────────────────────────────────┘
```

---

## Layer 1: Infrastructure & Config
**Graph Nodes:** 23 | **Issues Found:** 4

### Components
| Component | File | Graph Node ID | Status |
|-----------|------|---------------|--------|
| Async DB Engine | `backend/shared/db.py` | `db:AsyncEngine` | ✅ Fixed (NullPool) |
| Config Settings | `backend/shared/config.py` | `config:Settings` | 🔧 Needs defaults removed |
| Redis Stream | `backend/shared/stream.py` | `stream:RedisStreamClient` | ⚠️ Event emitter fix pending |
| Docker Compose | `infra/docker-compose.yml` | `infra:docker` | ⚠️ Missing backend healthcheck |

### Graph Query
```bash
# Find all files importing config or db
code-review-graph query --pattern "imports backend.shared.config"
code-review-graph query --pattern "imports backend.shared.db"
```

### Remediation
- [[HIGH-015]] Remove hardcoded DB password from config
- [[HIGH-016]] Remove hardcoded admin username
- [[HIGH-047]] Fix JWT secret caching at module level

---

## Layer 2: API Gateway & Auth
**Graph Nodes:** 31 | **Issues Found:** 7

### Components
| Component | File | Graph Node ID | Auth Coverage |
|-----------|------|---------------|---------------|
| Auth Router | `api/routes/auth.py` | `routes:auth` | Login/refresh only |
| Leads Router | `api/routes/leads.py` | `routes:leads` | ✅ CRIT-001 Fixed |
| Admin Router | `api/routes/admin.py` | `routes:admin` | ✅ Auth OK |
| Stats Router | `api/routes/stats.py` | `routes:stats` | 🔴 Missing auth |
| MCP Router | `api/routes/mcp.py` | `routes:mcp` | 🔴 Missing auth |
| MCP Server | `api/mcp_server.py` | `mcp:server` | 🔴 Dev mode bypass |

### Dependency Graph
```
main.py → leads.py → deps.py → auth.py → config.py
                    → admin.py → deps.py → auth.py
                    → stats.py → NO AUTH DEP
                    → mcp.py → NO AUTH DEP
```

### Remediation
- [[HIGH-018]] Remove JWT query param from `/auth/me`
- [[HIGH-019]] Enforce MCP auth (remove empty-key bypass)
- [[HIGH-020]] Add auth to stats endpoint

---

## Layer 3: Data Access Layer
**Graph Nodes:** 18 | **Issues Found:** 6

### Components
| Component | File | Graph Node ID | Issues |
|-----------|------|---------------|--------|
| Lead Model | `shared/models.py:Lead` | `models:Lead` | Missing columns, embedding |
| Post Model | `shared/models.py:Post` | `models:Post` | Missing updated_at |
| LeadRepo | `shared/repository.py:LeadRepo` | `repo:LeadRepo` | N+1 queries |
| FeedbackRepo | `shared/repository.py:FeedbackRepo` | `repo:FeedbackRepo` | Integer PK |
| QuotaRepo | `shared/repository.py:QuotaRepo` | `repo:QuotaRepo` | Integer PK |
| Migrations | `alembic/versions/*.py` | `migration:*` | CONCURRENTLY tx, column mismatch |

### Blast Radius Query
```bash
# What breaks if we change Lead model?
code-review-graph query --pattern "uses Lead" --from models:Lead
```

### Remediation
- [[CRIT-006]] Add embedding column ✅
- [[CRIT-007]] Fix CONCURRENTLY in transaction ✅
- [[CRIT-008]] Fix icp_score vs icp_fit_score ✅
- [[HIGH-021]] Add missing columns to Lead
- [[HIGH-022]] Add events relationship
- [[HIGH-023]] Add FK constraint to LeadDLQ
- [[HIGH-029]] Fix N+1 in LeadRepo.list_all()

---

## Layer 4: Business Logic & Services
**Graph Nodes:** 24 | **Issues Found:** 5

### Components
| Component | File | Graph Node ID | Consumers |
|-----------|------|---------------|-----------|
| Confidence | `services/confidence.py` | `svc:confidence` | gemini_service, dedup_service |
| Dedup Engine | `services/dedup_service.py` | `svc:dedup` | pipeline.py |
| Waterfall | `services/waterfall_enrichment.py` | `svc:waterfall` | pipeline.py |
| Personalization | `services/personalization.py` | `svc:personalization` | profile.py routes |
| Velocity | `services/velocity.py` | `svc:velocity` | profile.py routes |

### Call Graph
```
gemini_service.py → compute_confidence → confidence.py
pipeline.py → dedup_lead → dedup_service.py → find_duplicate
            → merge_leads → dedup_service.py
profile.py routes → get_personalized_leads → personalization.py
```

### Remediation
- [[CRIT-005]] Fix deleted model import ✅
- [[HIGH-027]] Move pipeline logic from routes to service
- [[HIGH-028]] Move profile scoring from routes to service
- [[HIGH-034]] Replace Redis KEYS with SCAN

---

## Layer 5: LLM Intelligence Layer
**Graph Nodes:** 44 | **Issues Found:** 6 | **Central Hub**

### Components
| Component | File | Graph Node ID | Purpose |
|-----------|------|---------------|---------|
| Gemini Service | `llm/gemini_service.py` | `llm:gemini` | Extraction, embeddings, vision |
| Cost Guard | `llm/cost_guard.py` | `llm:cost_guard` | Budget enforcement |
| Circuit Breaker | `llm/circuit_breaker.py` | `llm:circuit` | Resilience |
| Source Prompts | `llm/SOURCE_PROMPTS.py` | `llm:prompts` | 8 source-specific prompts |
| Schemas | `llm/schemas.py` | `llm:schemas` | AnalyzedLead Pydantic model |
| ICP Parser | `llm/gemini_service.py:parse_nl_icp` | `llm:icp_parser` | Natural language → structured |

### Dependency Graph (Blast Radius)
```
gemini_service.py (16 dependent edges)
  ├── CALLS_FROM
  │   ├── icp_service.py → parse_natural_language_icp
  │   ├── waterfall_enrichment.py → extract_lead
  │   ├── tracxn-actor → extract_lead
  │   ├── dpiit-actor → extract_lead
  │   └── mca21-actor → extract_lead
  ├── IMPORTS_FROM
  │   ├── SOURCE_PROMPTS.py
  │   ├── cost_guard.py
  │   ├── confidence.py (FIXED: was backend.llm.confidence)
  │   ├── vertexai.generative_models
  │   └── vertexai.language_models
  └── CONTAINS
      ├── extract_lead() → regex_fallback_extract → compute_confidence
      ├── get_embedding() → check_budget
      ├── extract_from_image() → check_budget
      └── parse_natural_language_icp() → check_budget
```

### Remediation
- [[CRIT-003]] Fix broken confidence import ✅
- [[CRIT-004]] Wrap sync calls in asyncio.to_thread() ✅
- [[HIGH-035]] Raise GeminiExtractionError instead of error dict

---

## Layer 6: Pipeline & Workers
**Graph Nodes:** 19 | **Issues Found:** 5

### Components
| Component | File | Graph Node ID | Pattern |
|-----------|------|---------------|---------|
| Celery App | `workers/pipeline.py` | `worker:celery` | Task chain + beat |
| Analyzer | `workers/analyzer.py` | `worker:analyzer` | 7-stage waterfall |
| Scorer | `workers/scorer.py` | `worker:scorer` | Composite scoring |
| Actors | `workers/actors.py` | `worker:actors` | Async task anti-pattern |
| DLQ Handler | `workers/dlq.py` | `worker:dlq` | Retry with backoff |

### Task Chain Topology
```
[Celery Beat 15min]
  → collect_and_publish
    → Redis Stream "lead:collected"
      → run_analysis_consumer
        → DB write
        → Redis Stream "lead:analyzed"
          → run_scoring_consumer
            → Redis Stream "lead:scored"
              → persist_scored_leads
                → PostgreSQL (final_score >= 40)
                → emit("lead_created")
                → emit("lead_enriched")
                → emit("lead_scored")
```

### Remediation
- [[CRIT-009]] Make emit() async ✅
- [[CRIT-010]] Fix Celery async anti-pattern ✅
- [[HIGH-033]] Fix DLQ signal handler
- [[HIGH-036]] Add retry counter to analyzer

---

## Layer 7: Telemetry & Observability
**Graph Nodes:** 12 | **Issues Found:** 3

### Components
| Component | File | Graph Node ID | Purpose |
|-----------|------|---------------|---------|
| Eval Runner | `eval/run_eval.py` | `eval:runner` | Precision measurement |
| Ground Truth | `eval/ground_truth.json` | `eval:gt` | 50 canonical cases |
| Daily Report | `workers/pipeline.py:daily_report` | `worker:daily` | Metrics aggregation |
| Sentry | `shared/logging_config.py` | `obs:sentry` | Error tracking |

### Remediation
- Connect eval runner to real Gemini extraction (currently mock data)
- Fix Sentry DSN logging leak

---

## Stack Execution Order

The GitNexus Stack enforces **bottom-up remediation**:

```
Phase 1: Layer 1 → Infrastructure (config fixes)
Phase 2: Layer 2 → API Gateway (auth fixes)
Phase 3: Layer 3 → Data Access (model fixes)
Phase 4: Layer 4 → Business Logic (service fixes)
Phase 5: Layer 5 → LLM Intelligence (extraction fixes)
Phase 6: Layer 6 → Pipeline & Workers (async fixes)
Phase 7: Layer 7 → Telemetry (eval fixes)
```

**Why bottom-up?** Fixing Layer 3 (models) before Layer 5 (LLM) ensures the data structures exist before the LLM tries to populate them. Fixing Layer 1 (config) before Layer 2 (auth) ensures secrets are properly configured before auth starts using them.

---

## GitNexus Query Cheat Sheet

### Before Any Fix
```bash
# Find blast radius
code-review-graph get_impact_radius --file backend/llm/gemini_service.py

# Find all callers
code-review-graph query --pattern "calls extract_lead"

# Find tests
code-review-graph query --pattern "tests_for extract_lead"
```

### After Any Fix
```bash
# Verify no regressions
code-review-graph detect_changes --from HEAD~1

# Check test coverage
code-review-graph query --pattern "tests_for" --file backend/llm/gemini_service.py
```

---

## Integration with Memory Palace

Each layer maps to a room:

| Layer | Memory Palace Room | Anchor |
|-------|-------------------|--------|
| Layer 1 | The-Citadel (foundation) | Floor tiles |
| Layer 2 | The-Gatehouse | Gate guards |
| Layer 3 | The-Archive | Scrolls & bindings |
| Layer 4 | The-Forge (anvil) | Anvil surface |
| Layer 5 | The-Forge (furnace) | Furnace core |
| Layer 6 | The-Orrery | Gears & orbits |
| Layer 7 | The-Citadel (ceiling) | Ceiling mural |

---

*Generated from code-review-graph analysis: 44 LLM nodes, 16 dependent edges, 5 calling files.*

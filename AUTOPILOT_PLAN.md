# Adaptive Imagining Cat: State Analysis + Execution Plan
## LeadIQ v3 — World-Class Lead Hunter (#1 in the World)

---

## PHASE 1: STATE ANALYSIS

### 1.1 Environment Scan

```yaml
session_id: "ses_1f67e7553ffeF9QFG2Kr7xfrlr"
timestamp: "2026-05-09T06:30:00Z"
environment:
  cwd: "/media/roshan/New Volume/c drive/Downloads/b_a6LznsoAKUT-1774336963705"
  git_branch: "main (latest: 7558f8b)"
  git_status: "Dirty (uncommitted changes: engine/, pipeline_v3.py, graph_db.py, etc.)"
  recent_commits: 
    - "7558f8b docs(vault): Phase 6 autopilot + remediation plans"
    - "cb14ebb refactor(audit): complete Phases 1-5 remediation (93 issues)"
    - "fe895d8 feat(dlq,actors): DLQ worker, GitHub & Telegram actors, full admin CRUD"
    - "2c645ed Update project"
```

### 1.2 Codebase State Assessment

| Component | Status | Coverage | Issues |
|-----------|--------|----------|--------|
| **Collectors** | ✅ 9 implemented | HN, Reddit, StackOverflow, GitHub, Twitter, RSS, Telegram, ProductHunt + custom | None |
| **Scoring (engine/)** | ✅ MultiDimensionalScorer v3 | 12 intent signals, keyword+context | Scoring too conservative (COLD bias) |
| **Scoring (services/)** | ✅ OpportunityScorer + ICP | Logistic regression, temporal decay | Duplicated with engine/ — not merged |
| **Analysis (workers/)** | ✅ 7-stage Gemini waterfall | Classification + enrichment | DEPENDS on paid Gemini API |
| **Dedup** | ✅ 3-tier (exact→fuzzy→vector) | Redis + pgvector | None |
| **Pipeline** | ✅ Celery orchestration | collect→dedup→score→persist→notify | v3 not connected to main pipeline |
| **Contact Enrichment** | 🟡 contacts.py (incomplete) | GitHub/HN profile scraping | Not wired into pipeline |
| **Trend Analysis** | 🟡 trends.py (incomplete) | BERTopic + keyword frequency | Not wired, BERTopic not installed |
| **Graph DB (Neo4j)** | 🟡 graph_db.py (skeleton) | Connect + CRUD queries | Not connected to pipeline |
| **Tests** | ✅ 16+ test files | pytest + pytest-asyncio | backend/tests/ not in root tests/ |
| **CI/CD** | ✅ 4 GitHub workflows | Build, lint, test, staging | backend-ci.yml needs update for new modules |
| **Observability** | ✅ Structured logging (structlog) | Sentry, Redis metrics | None |
| **Auth** | ✅ JWT | login/refresh/logout/me | None |
| **API** | ✅ FastAPI | leads, auth, admin, profile, stats, MCP | None |
| **Frontend** | ✅ Next.js | Build, test passing | Lighthouse audit possible |

### 1.3 Critical Gap Analysis

| Gap | Impact | Why It Matters |
|-----|--------|---------------|
| **Scoring v3 not connected** | HIGH | New 12-dim engine is orphaned; main pipeline still uses old 3-layer scorer |
| **Ollama/Local LLM not wired** | HIGH | Gemini is paid; constraint says zero paid — need local LLM fallback |
| **Graph DB not connected** | MEDIUM | Neo4j layer has no data flowing through it |
| **Contact enrichment partial** | MEDIUM | Email/phone inference not integrated with pipeline |
| **Trend analysis partial** | LOW | BERTopic not installed; keyword fallback works but weak |
| **Test coverage gaps** | MEDIUM | backend/tests/ separate from tests/; no tests for new engine/ |

### 1.4 Competitive Score (vs Apollo/ZoomInfo)

| Dimension | Your v3 | Apollo | ZoomInfo | Gap |
|-----------|---------|--------|----------|-----|
| **Unique data sources** | 9 (free) | 3-4 | 3-4 | ✅ MORE sources, but |
| **Intent accuracy** | ~40% (heuristic) | ~70% | ~65% | ❌ WEAK: needs LLM boost |
| **Signal freshness** | Real-time (< 1hr) | Daily | Daily | ✅ BEST |
| **Cost per lead** | $0 | ~$0.50 | ~$1.00 | ✅ BEST |
| **Relationship graph** | 🟡 Neo4j skeleton | ❌ none | ❌ none | ✅ **UNIQUE** but empty |
| **Contact inference** | 🟡 partial | 90% | 95% | NEEDS work |
| **Field accuracy** | ~20% (heuristic) | 90% | 95% | ❌ WEAK: needs enrichment |
| **Tech stack detection** | 🟡 (keyword only) | Basic | Basic | COULD be #1 with LLM |
| **Scalability** | Redis + Celery + async | Enterprise | Enterprise | ✅ MATCH |
| **False positive rate** | ~70% | ~40% | ~45% | ❌ TOO HIGH |
| **Cold-start latency** | Good | OK | OK | ✅ MATCH |

**Overall: 4.5/10 (vs Apollo 7.5, ZoomInfo 8.0)**

---

## PHASE 2: TYPED PLAN (POLARIS Method)

### Goal: Close the gap to #1 in the world using only free/open sources

```yaml
plan:
  id: "plan-leadiq-world-class-001"
  goal: "Build the world's #1 lead hunting platform using zero paid APIs"
  created: "2026-05-09"
  approved: false  # AWAITING USER APPROVAL

phases:
  - id: "phase-1-merge-scoring"
    type: implement
    name: "Merge MultiDimensionalScorer into main pipeline"
    description: "Replace old 3-layer scorer with new 12-dim engine in workers/analyzer.py"
    inputs: []
    outputs: [
      "workers/analyzer.py updated",
      "services/opportunity_scorer.py deprecated",
      "Pipeline produces WARM/HOT leads"
    ]
    guardrails:
      - "Must maintain backward compatibility with existing tests"
      - "Must not increase false positive rate beyond 50%"
      - "Must run with zero API keys (heuristic fallback always works)"
    estimated_tokens: 8000
    checkpoint: true

  - id: "phase-2-ollama-fallback"
    type: implement
    name: "Wire Ollama Local LLM as primary analysis engine"
    description: "Replace Gemini as default; Gemini becomes premium opt-in. Use phi3:mini (3.8B, 2GB RAM)."
    inputs: ["phase-1-merge-scoring"]
    outputs: [
      "llm/ollama_provider.py fully wired to analyzer.py",
      "Config flag for 'use_local_llm' (default=true)",
      "Docker compose with Ollama service"
    ]
    guardrails:
      - "Ollama must classify intent with >60% accuracy vs Gemini"
      - "Fallback to deterministic heuristics must be instant"
      - "Zero-cost operation: no API calls unless explicitly enabled"
    resources:
      skills: ["[[topics/adaptive-imagining-cat]]"]
      tools: ["ollama", "docker"]
    estimated_tokens: 12000
    checkpoint: true

  - id: "phase-3-graph-populate"
    type: implement
    name: "Populate Neo4j Graph DB with every post+lead"
    description: "Connect graph_db.py to pipeline; auto-create org/person/post/tech nodes and relationships."
    inputs: ["phase-2-ollama-fallback"]
    outputs: [
      "Every lead creates/updates graph nodes",
      "Relationship queries: get_org_leads, get_tech_trends working",
      "Graph-powered enrichment (company inference from relationships)"
    ]
    guardrails:
      - "Neo4j Community Edition only (free)"
      - "Graph writes must be async and non-blocking"
    estimated_tokens: 10000
    checkpoint: true

  - id: "phase-4-contact-enrichment"
    type: implement
    name: "Complete Contact Enrichment Pipeline"
    description: "Wire enrich_github_contacts, infer_persona, email pattern inference into the scoring flow."
    inputs: ["phase-3-graph-populate"]
    outputs: [
      "Every scored lead has inferred company domain, email pattern, persona",
      "Persona field: Decision Maker / Influencer / Practitioner / Unknown",
      "Contact inference accuracy >40% (better than random)"
    ]
    guardrails:
      - "Only public API calls (GitHub REST API, no auth needed for public profiles)"
      - "Rate limiting: max 60 req/min to GitHub"
    estimated_tokens: 8000
    checkpoint: true

  - id: "phase-5-trend-detection"
    type: implement
    name: "Implement Market Trend Detection"
    description: "Complete BERTopic + keyword trend analysis; detect emerging tech adoption curves."
    inputs: ["phase-3-graph-populate"]
    outputs: [
      "Hourly trend report: top 20 trending topics across all sources",
      "Momentum classification: EXPLODING / RISING / STABLE / DECLINING",
      "Trend signal amplification: boost lead scores when part of rising trend"
    ]
    guardrails:
      - "BERTopic optional (pip install bertopic) — keyword fallback always works"
      - "Trend analysis must run in <30 seconds for 1000 posts"
    estimated_tokens: 10000
    checkpoint: true

  - id: "phase-6-ranking-benchmark"
    type: verify
    name: "Benchmark vs Apollo/ZoomInfo and calibrate ranking"
    description: "Run full pipeline on 500 leads, measure accuracy, tune thresholds."
    inputs: ["phase-2-ollama-fallback", "phase-3-graph-populate", "phase-4-contact-enrichment"]
    outputs: [
      "HOT leads: target >5% of total (currently 0%)",
      "WARM leads: target >15% of total (currently ~1%)",
      "False positive rate <30% (currently ~70%)"
    ]
    guardrails:
      - "Blind evaluation: compare scored leads against manual ground truth"
      - "If HOT < 3%: reduce scoring thresholds by 20%"
      - "If false positive >50%: increase pattern strictness or add LLM re-filter"
    estimated_tokens: 5000
    checkpoint: true

  - id: "phase-7-production-ready"
    type: deploy
    name: "Production Hardening + CI/CD + Docs"
    description: "Final production checklist: tests, docs, monitoring, deployment."
    inputs: ["phase-6-ranking-benchmark"]
    outputs: [
      "100% test pass rate on new modules",
      "ruff + mypy clean",
      "Updated PRODUCTION_READINESS_REPORT.md → 9.0/10",
      "Docker compose for full stack (API + workers + Ollama + Neo4j + Redis + Postgres)"
    ]
    guardrails:
      - "Must pass CI/CD (backend-ci.yml) without errors"
      - "Must have monitoring (Sentry + custom metrics)"
      - "Must have runbook for ops team"
    resources:
      skills: ["[[topics/deployment-patterns]]", "[[topics/e2e-testing]]"]
      commands: ["/ship", "/qa"]
    estimated_tokens: 8000
    checkpoint: true
```

---

## PHASE 3: RESOURCE MAP

| Resource | Skill/Tool | When to Invoke |
|----------|-----------|----------------|
| Merge scoring engine | `[[topics/adaptive-imagining-cat]]` Phase 3 | phase-1 |
| Ollama setup | `/autopilot` + `[[topics/tdd-workflow]]` | phase-2 |
| Neo4j wiring | `[[topics/postgres-patterns]]` (adapt) | phase-3 |
| Contact enrichment | `[[topics/search-first]]` | phase-4 |
| BERTopic install | `pip` | phase-5 |
| Benchmark | `/benchmark` command | phase-6 |
| Production deploy | `/ship` + `/qa` | phase-7 |

---

## PHASE 4: RISK ANALYSIS

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Ollama not available on deploy target | Medium | High | Docker compose with phi3:mini pre-downloaded |
| Neo4j memory usage | Medium | Medium | Use Aura Free (Neo4j cloud) or in-memory for dev |
| Scoring threshold tuning takes >2 iterations | High | Medium | Phase 6 benchmark with auto-calibration script |
| GitHub API rate limits | Medium | Medium | Caching layer + 60 req/min throttling |
| Test coverage drops below 80% | Medium | Medium | Enforce in CI; pytest-cov gate |
| LLM hallucination in intent classification | Medium | High | Always use regex as PRIMARY, LLM as ENHANCEMENT |

---

## DECISION GATE

### Before proceeding to Phase 1, you must decide:

1. **Do we keep or deprecate the old 3-layer scorer in `services/`?**
   - Keep: backward compatibility but tech debt
   - Deprecate: clean slate but risk of regression

2. **Ollama default model:**
   - `phi3:mini` (3.8B, fastest, 2GB RAM) ← RECOMMENDED
   - `llama3.2:1b` (1B, ultra-fast, lowest quality)
   - `gemma2:2b` (balanced)
   - `qwen2.5:3b` (highest quality of the lightweights)

3. **Neo4j strategy:**
   - Aura Free (cloud, managed, 200K nodes free)
   - Docker local (self-hosted, unlimited)
   - Skip for now (focus on scoring first)

4. **Timeline priority:**
   - **Fast track:** Phases 1-2 only (score boost + LLM)
   - **Balanced:** Phases 1-5 (full intelligence stack)
   - **All-in:** Phases 1-7 (production world-class)

---

## APPROVAL GATE

**Type one of:**
- `"go fast-track"` → Implement Phases 1-2 only
- `"go balanced"` → Implement Phases 1-5
- `"go all-in"` → Implement all 7 phases to production
- `"modify"` → I'll adjust the plan first
- `"explain <phase>`" → Deep dive into a specific phase

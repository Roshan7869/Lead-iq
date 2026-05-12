# LeadIQ: 100-Layer Implementation Plan
## paper2code + adaptive-imagining-cat + Multi-LLM Orchestration

---

## 1. Executive Summary

This plan implements a **100-layer heterogeneous architecture** for LeadIQ, combining:
- **paper2code**: Converting 10+ research papers into production code
- **adaptive-imagining-cat**: State Analysis → Typed Plan → Resource Map → Autopilot Execute → Block Verify → Audit
- **NEXUS v3**: Intelligent resource routing across 1,097 indexed skills
- **Multi-LLM**: Kimi K2.6 (orchestrator) + NVIDIA NIM/DeepSeek (reasoning) + Gemini (24/7 generation)

**Deployment Target**: Vercel (Frontend) + Railway (Backend) + Supabase (Database)
**Total Cost**: $5/month minimum
**Timeline**: 4-6 weeks
**Research Papers**: 10 verified papers (NeurIPS, KDD, ACL, EMNLP)

---

## 2. Multi-LLM Architecture

```
User Request
    │
    ▼
┌──────────────────┐
│  Kimi K2.6       │─── Orchestrator (always on via OpenCode)
│  (This session)  │─── Route task to best LLM
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐  ┌────────┐
│NVIDIA  │  │ Gemini │
│NIM     │  │(GCP   │
│Free    │  │Trial) │
│Tier    │  │        │
└───┬────┘  └───┬────┘
    │           │
    ▼           ▼
┌────────┐  ┌────────┐
│DeepSeek│  │Gemini  │
│(reason)│  │Flash   │
│Llama   │  │Pro     │
│Mistral │  │        │
└────────┘  └────────┘
```

### Task Assignment Matrix

| Task | Primary LLM | API | Secondary | Fallback |
|------|-----------|-----|-----------|----------|
| Research paper implementation | **Kimi K2.6** | OpenCode | DeepSeek | Gemini |
| Complex reasoning (scoring) | **DeepSeek** | NVIDIA NIM | Kimi K2.6 | Gemini |
| Outreach generation (24/7) | **Gemini Flash** | GCP | DeepSeek | Kimi K2.6 |
| Web scraping code | **Kimi K2.6** | OpenCode | Llama (NIM) | Gemini |
| NER/Entity extraction | **DeepSeek** | NVIDIA NIM | Kimi K2.6 | Gemini |
| Frontend/React code | **Kimi K2.6** | OpenCode | Gemini | DeepSeek |
| Testing/QA | **Kimi K2.6** | OpenCode | Gemini | DeepSeek |
| Gov scheme scraping | **Kimi K2.6** | OpenCode | — | — |
| Funding detection NER | **DeepSeek** | NVIDIA NIM | Gemini | Kimi K2.6 |
| URL validation | **Kimi K2.6** | OpenCode | — | — |

---

## 3. 100-Layer Component Map

### Layers 1-10: Data Collection & Scraping

| Layer | Name | NEXUS Skill | LLM | Frontend | Backend |
|-------|------|-------------|-----|----------|---------|
| 1 | Static Scraper | `scrape` | Kimi | — | `collectors/base.py` |
| 2 | Dynamic Scraper | `browse` | Kimi | — | `collectors/dynamic.py` |
| 3 | API Aggregation | `callfn-api-helper` | Kimi | — | `api/router.py` |
| 4 | Anti-Detection | `security-review` | Kimi | — | `services/antibot.py` |
| 5 | Distributed Crawl | `swarm-orchestration` | DeepSeek | — | `workers/distributed.py` |
| 6 | Politeness Engine | `careful` | Kimi | — | `services/politeness.py` |
| 7 | SimHash Dedup | `search-first` | DeepSeek | — | `services/deduper.py` |
| 8 | Proxy Rotation | `mesh-coordinator` | Kimi | — | `services/proxy.py` |
| 9 | CAPTCHA Solve | `security-review` | Gemini | — | `services/captcha.py` |
| 10 | Monitor/Alert | `benchmark` | Kimi | `StatusBadge.tsx` | `services/monitor.py` |

### Layers 11-20: NLP & Signal Detection

| Layer | Name | NEXUS Skill | LLM | Frontend | Backend |
|-------|------|-------------|-----|----------|---------|
| 11 | spaCy NER | `agentdb-vector-search` | DeepSeek | — | `services/ner.py` |
| 12 | BERT Intent | `iterative-retrieval` | DeepSeek | — | `services/intent.py` |
| 13 | RoBERTa Sentiment | `reasoningbank-intelligence` | DeepSeek | — | `services/sentiment.py` |
| 14 | BERTopic | `search-first` | Gemini | `TopicCloud.tsx` | `services/topic_model.py` |
| 15 | Event Extraction | `iterative-retrieval` | DeepSeek | — | `services/event_extract.py` |
| 16 | Relation Extraction | `iterative-retrieval` | DeepSeek | — | `services/relation.py` |
| 17 | KeyBERT | `iterative-retrieval` | Gemini | `KeywordList.tsx` | `services/keywords.py` |
| 18 | Language Detect | `search-first` | Kimi | — | `services/lang_detect.py` |
| 19 | BART Summarize | `search-first` | Gemini | `SummaryCard.tsx` | `services/summarizer.py` |
| 20 | Zero-shot Classify | `agentdb-vector-search` | DeepSeek | — | `services/zero_shot.py` |

### Layers 21-30: Lead Scoring & Ranking

| Layer | Name | NEXUS Skill | LLM | Frontend | Backend |
|-------|------|-------------|-----|----------|---------|
| 21 | Feature Engineering | `search-first` | DeepSeek | — | `services/feature_eng.py` |
| 22 | XGBoost Scorer | `wiki-credibility-scoring` | DeepSeek | `ScoreChart.tsx` | `services/scorer.py` |
| 23 | Temporal Decay | `reasoningbank-intelligence` | DeepSeek | `DecayGraph.tsx` | `services/temporal.py` |
| 24 | BTYD CLV | `reasoningbank-intelligence` | DeepSeek | `CLVCard.tsx` | `services/clv.py` |
| 25 | AHP MCDM | `search-first` | DeepSeek | `RankTable.tsx` | `services/mcdm.py` |
| 26 | ICP Matching | `agentdb-vector-search` | Kimi | `ICPFitBadge.tsx` | `services/icp_match.py` |
| 27 | SHAP Explain | `verification-quality` | DeepSeek | `SHAPChart.tsx` | `services/shap.py` |
| 28 | A/B Testing | `qa` | Kimi | `ABTestPanel.tsx` | `services/ab_test.py` |
| 29 | Online Learning | `reasoningbank-agentdb` | DeepSeek | — | `services/online_learn.py` |
| 30 | Graph Networks | `swarm-orchestration` | DeepSeek | `GraphView.tsx` | `services/graph_nets.py` |

### Layers 31-40: Real-Time Event Processing

| Layer | Name | NEXUS Skill | LLM | Frontend | Backend |
|-------|------|-------------|-----|----------|---------|
| 31 | Redis Streams | `stream-chain` | Kimi | `EventLog.tsx` | `workers/*.py` |
| 32 | Event Sourcing | `stream-chain` | Kimi | — | `services/event_source.py` |
| 33 | CDC | `stream-chain` | Kimi | — | `services/cdc.py` |
| 34 | Kafka | `stream-chain` | Kimi | — | `services/kafka.py` |
| 35 | Celery Workers | `stream-chain` | Kimi | — | `workers/celery.py` |
| 36 | DLQ | `careful` | Kimi | — | `workers/dlq.py` |
| 37 | Idempotency | `stream-chain` | Kimi | — | `services/idempotency.py` |
| 38 | Stream Replay | `stream-chain` | Kimi | — | `services/replay.py` |
| 39 | Stream Monitor | `benchmark` | Kimi | — | `services/stream_monitor.py` |
| 40 | Backpressure | `stream-chain` | Kimi | — | `services/backpressure.py` |

### Layers 41-50: LLM & AI Integration

| Layer | Name | NEXUS Skill | LLM | Frontend | Backend |
|-------|------|-------------|-----|----------|---------|
| 41 | Multi-LLM Router | `cost-aware-llm-pipeline` | Kimi | `ModelBadge.tsx` | `services/llm_router.py` |
| 42 | Circuit Breaker | `guard` | Kimi | — | `llm/circuit_breaker.py` |
| 43 | Prompt Version | `verification-loop` | Kimi | — | `llm/prompt_versioning.py` |
| 44 | Cost Guard | `careful` | Kimi | `CostBadge.tsx` | `llm/cost_guard.py` |
| 45 | Fallback Chain | `verification-quality` | Kimi | — | `llm/fallback_chain.py` |
| **46** | **🔥 RAG** | **`agentdb-vector-search`** | **Kimi + DeepSeek** | **`RagBadge.tsx`** | **`services/rag_*.py`** |
| 47 | LLM Eval | `benchmark-models` | DeepSeek | `ScoreTable.tsx` | `services/llm_eval.py` |
| 48 | Prompt Injection | `security-scan` | DeepSeek | — | `services/injection_detect.py` |
| 49 | Output Validation | `verification-loop` | Kimi | — | `services/output_validate.py` |
| 50 | LLM Cache | `agentdb-optimization` | Kimi | — | `services/llm_cache.py` |

### Layers 51-60: Job Market Intelligence

| Layer | Name | NEXUS Skill | LLM | Frontend | Backend |
|-------|------|-------------|-----|----------|---------|
| 51 | Job Aggregation | `skill-social-media-dashboard` | Kimi | — | `collectors/job_signals.py` |
| 52 | Skills Taxonomy | `search-first` | DeepSeek | — | `services/skills_taxonomy.py` |
| 53 | Salary Benchmark | `mesh-coordinator` | DeepSeek | — | `services/salary.py` |
| 54 | Hiring Velocity | `reasoningbank-intelligence` | DeepSeek | `VelocityChart.tsx` | `services/velocity.py` |
| 55 | Job Alerts | `skill-social-media-dashboard` | Kimi | `JobAlertPanel.tsx` | `services/job_alerts.py` |
| 56 | Resume Parse | `iterative-retrieval` | DeepSeek | — | `services/resume_parser.py` |
| 57 | Semantic Match | `agentdb-vector-search` | DeepSeek | — | `services/semantic_match.py` |
| 58 | Auto Outreach | `cost-aware-llm-pipeline` | Gemini | — | `services/auto_outreach.py` |
| 59 | Skill Trends | `reasoningbank-intelligence` | DeepSeek | `TrendChart.tsx` | `services/skill_trends.py` |
| 60 | Talent Map | `swarm-orchestration` | DeepSeek | `TalentMap.tsx` | `services/talent_map.py` |

### Layers 61-70: Startup & Funding

| Layer | Name | NEXUS Skill | LLM | Frontend | Backend |
|-------|------|-------------|-----|----------|---------|
| 61 | Funding Detection | `iterative-retrieval` | DeepSeek | `FundingCard.tsx` | `collectors/funding_news.py` |
| 62 | VC Deal Flow | `iterative-retrieval` | DeepSeek | `VCDashboard.tsx` | `services/vc_intel.py` |
| 63 | Gov Scheme Scrape | `scrape` | Kimi | `SchemeCard.tsx` | `collectors/government_schemes.py` |
| 64 | Startup News | `search-first` | DeepSeek | `NewsFeed.tsx` | `collectors/startup_news.py` |
| 65 | Accelerator Track | `search-first` | DeepSeek | — | `services/accelerator.py` |
| 66 | Patent/IP Track | `iterative-retrieval` | DeepSeek | — | `services/patent_tracker.py` |
| 67 | Social Signal | `skill-social-media-dashboard` | DeepSeek | `SocialChart.tsx` | `services/social_signals.py` |
| 68 | Competitor Analysis | `iterative-retrieval` | DeepSeek | `CompetitorTable.tsx` | `services/competitor.py` |
| 69 | Market Gap | `search-first` | DeepSeek | `GapAnalysis.tsx` | `services/market_gap.py` |
| 70 | Investment Thesis | `search-first` | DeepSeek | — | `services/thesis_gen.py` |

### Layers 71-80: Trust & Verification

| Layer | Name | NEXUS Skill | LLM | Frontend | Backend |
|-------|------|-------------|-----|----------|---------|
| 71 | URL Trust Score | `verification-quality` | Kimi | `TrustBadge.tsx` | `services/url_validator.py` |
| 72 | Source Credibility | `verification-quality` | DeepSeek | `CredScore.tsx` | `services/credibility.py` |
| 73 | Fact-Checking | `iterative-retrieval` | DeepSeek | `FactCheck.tsx` | `services/fact_check.py` |
| 74 | Misinfo Detect | `security-scan` | DeepSeek | `MisinfoAlert.tsx` | `services/misinfo.py` |
| 75 | SSL Verify | `verification-quality` | Kimi | `SSLBadge.tsx` | `services/ssl_verify.py` |
| 76 | Domain Age | `verification-quality` | Kimi | — | `services/domain_age.py` |
| 77 | Content Freshness | `search-first` | Kimi | `FreshnessTag.tsx` | `services/freshness.py` |
| 78 | Reputation | `wiki-credibility-scoring` | DeepSeek | `RepScore.tsx` | `services/reputation.py` |
| 79 | GDPR Check | `security-scan` | Kimi | — | `services/gdpr.py` |
| 80 | Copyright Check | `security-scan` | Kimi | — | `services/copyright.py` |

### Layers 81-90: Frontend-Backend Integration

| Layer | Name | NEXUS Skill | LLM | Frontend | Backend |
|-------|------|-------------|-----|----------|---------|
| 81 | React Query | `react-query-api-layer` | Kimi | `useQuery hooks` | `api/routes/*.py` |
| 82 | Next.js Router | `flow-nexus-neural` | Kimi | `app/(routes)` | — |
| 83 | Design System | `spec-driven-development` | Kimi | `ui/*.tsx` | — |
| 84 | Real-time UI | `stream-chain` | Kimi | `useLiveFeed` | `api/routes/live_feed.py` |
| 85 | Optimistic Update | `react-query-api-layer` | Kimi | `useMutation` | — |
| 86 | Error Boundary | `guard` | Kimi | `error.tsx` | — |
| 87 | Loading Skeleton | `react-query-api-layer` | Kimi | `loading.tsx` | — |
| 88 | Toast Notif | `react-query-api-layer` | Kimi | `sonner.tsx` | — |
| 89 | Dark Mode | `spec-driven-development` | Kimi | `theme-provider.tsx` | — |
| 90 | Responsive | `spec-driven-development` | Kimi | `tailwind.config.ts` | — |

### Layers 91-100: Production & Deployment

| Layer | Name | NEXUS Skill | LLM | Frontend | Backend |
|-------|------|-------------|-----|----------|---------|
| 91 | Docker Compose | `land-and-deploy` | Kimi | — | `infra/docker-compose.yml` |
| 92 | GitHub Actions | `github-workflows` | Kimi | — | `.github/workflows/ci.yml` |
| 93 | Kubernetes | `mesh-coordinator` | Kimi | — | `infra/k8s/*.yaml` |
| 94 | Env Management | `land-and-deploy` | Kimi | — | `.env.*` |
| 95 | Health Checks | `qa` | Kimi | `HealthDashboard.tsx` | `api/health.py` |
| 96 | Rate Limit | `careful` | Kimi | — | `services/rate_limit.py` |
| 97 | Observability | `benchmark` | Kimi | `MetricsDashboard.tsx` | `services/logging.py` |
| 98 | Alerting | `benchmark` | Kimi | — | `services/alerting.py` |
| 99 | Backup/Recovery | `careful` | Kimi | — | `services/backup.py` |
| 100 | Security Harden | `security-scan` | Kimi | — | `services/security.py` |

---

## 4. paper2code Pipeline

For each research paper, execute:

```
[Paper URL] → Phase 0 (Reference Search) → Phase 1 (Algorithm Extraction) 
→ Phase 2 (Concept Analysis) → Phase 3 (Code Planning) → Phase 4 (Implementation)
```

### Papers to Implement

| # | Paper | URL | Tier | NEXUS Route | Assigned LLM |
|---|-------|-----|------|-------------|--------------|
| 1 | **RAG** — Lewis et al. NeurIPS 2020 | arxiv.org/abs/2005.11401 | P0 | `agentdb-vector-search` | Kimi K2.6 |
| 2 | **Sentence-BERT** — Reimers & Gurevych 2019 | arxiv.org/abs/1908.10084 | P0 | `agentdb-vector-search` | Kimi K2.6 |
| 3 | **XGBoost** — Chen & Guestrin KDD 2016 | arxiv.org/abs/1603.02754 | P0 | `wiki-credibility-scoring` | DeepSeek (NVIDIA) |
| 4 | **BERT** — Devlin et al. NAACL 2019 | arxiv.org/abs/1810.04805 | P1 | `agentdb-vector-search` | DeepSeek (NVIDIA) |
| 5 | **RoBERTa** — Liu et al. 2019 | arxiv.org/abs/1907.11692 | P1 | `reasoningbank-intelligence` | DeepSeek (NVIDIA) |
| 6 | **BERTopic** — Grootendorst 2022 | arxiv.org/abs/2203.05794 | P1 | `search-first` | Gemini |
| 7 | **Faiss** — Douze et al. 2024 | arxiv.org/abs/2401.08281 | P0 | `agentdb-performance-optimization` | Kimi K2.6 |
| 8 | **SHAP** — Lundberg & Lee 2017 | arxiv.org/abs/1705.07874 | P2 | `verification-quality` | DeepSeek (NVIDIA) |
| 9 | **DyGIE++** — Wadden et al. 2019 | arxiv.org/abs/1909.03546 | P2 | `iterative-retrieval` | Gemini |
| 10 | **Hawkes Processes** — | | P2 | `reasoningbank-intelligence` | DeepSeek (NVIDIA) |

---

## 5. adaptive-imagining-cat Execution DAG

```yaml
plan_id: "leadiq-100-layer-implementation"
goal: "Implement full 100-layer architecture with paper2code + multi-LLM"
estimated_phases: 12
estimated_duration: 4-6 weeks
estimated_tokens: 500,000+

phases:
  # P0: Core (Week 1)
  - id: "phase-1-rag-core"
    type: implement
    name: "RAG Implementation (paper2code: Lewis et al. 2020)"
    inputs: []
    outputs:
      - backend/services/rag_chunker.py
      - backend/services/rag_embedder.py
      - backend/services/rag_indexer.py
      - backend/services/rag_retriever.py
      - backend/services/outreach_rag.py
      - src/components/RagBadge.tsx
    nexus_skill: "agentdb-vector-search"
    paper2code: "arxiv.org/abs/2005.11401"
    llm: "Kimi K2.6 (coding) + DeepSeek (algorithm optimization)"
    estimated_tokens: 15000

  - id: "phase-2-multi-llm"
    type: implement
    name: "Multi-LLM Router"
    inputs: ["phase-1"]
    outputs:
      - backend/services/llm_router.py
      - backend/api/routes/llm.py
    nexus_skill: "cost-aware-llm-pipeline"
    llm: "Kimi K2.6"
    estimated_tokens: 8000

  - id: "phase-3-url-validator"
    type: implement
    name: "URL Trust Validator"
    inputs: ["phase-2"]
    outputs:
      - backend/services/url_validator.py
      - src/components/UrlTrustBadge.tsx
    nexus_skill: "verification-quality"
    llm: "Kimi K2.6"
    estimated_tokens: 6000

  # P1: Intelligence (Week 2)
  - id: "phase-4-gov-scraper"
    type: implement
    name: "Government Scheme Scraper"
    inputs: ["phase-3"]
    outputs:
      - backend/collectors/government_schemes.py
      - src/app/schemes/page.tsx
    nexus_skill: "scrape"
    llm: "Kimi K2.6 (scraping) + DeepSeek (NLP extraction)"
    estimated_tokens: 10000

  - id: "phase-5-funding-detector"
    type: implement
    name: "Funding Round Detector (paper2code: Event Extraction)"
    inputs: ["phase-4"]
    outputs:
      - backend/collectors/funding_news.py
      - backend/services/funding_extractor.py
      - src/app/funding/page.tsx
    nexus_skill: "iterative-retrieval"
    paper2code: "arxiv.org/abs/1909.03546"
    llm: "DeepSeek (NER) + Gemini (summarization)"
    estimated_tokens: 12000

  - id: "phase-6-job-intelligence"
    type: implement
    name: "Job Market Intelligence"
    inputs: ["phase-5"]
    outputs:
      - backend/collectors/job_signals.py
      - src/app/jobs/page.tsx
    nexus_skill: "skill-social-media-dashboard"
    llm: "Kimi K2.6 (scraping) + DeepSeek (trend analysis)"
    estimated_tokens: 8000

  # P2: Advanced (Week 3)
  - id: "phase-7-advanced-nlp"
    type: implement
    name: "Advanced NLP Stack (paper2code: BERT, RoBERTa, BERTopic)"
    inputs: ["phase-6"]
    outputs:
      - backend/services/sentiment.py (RoBERTa)
      - backend/services/topic_model.py (BERTopic)
      - backend/services/intent.py (BERT)
      - backend/services/ner.py (spaCy)
    nexus_skill: "iterative-retrieval"
    paper2code: "arxiv.org/abs/1907.11692, arxiv.org/abs/2203.05794"
    llm: "DeepSeek (NVIDIA NIM)"
    estimated_tokens: 20000

  - id: "phase-8-scoring-stack"
    type: implement
    name: "ML Scoring Stack (paper2code: XGBoost + SHAP + BTYD)"
    inputs: ["phase-7"]
    outputs:
      - backend/services/scorer.py (XGBoost)
      - backend/services/shap.py (SHAP explainability)
      - backend/services/clv.py (BTYD)
      - backend/services/mcdm.py (AHP)
    nexus_skill: "wiki-credibility-scoring"
    paper2code: "arxiv.org/abs/1603.02754, arxiv.org/abs/1705.07874"
    llm: "DeepSeek (NVIDIA NIM)"
    estimated_tokens: 18000

  # P3: Integration (Week 4)
  - id: "phase-9-frontend-integration"
    type: implement
    name: "Frontend-Backend Integration"
    inputs: ["phase-8"]
    outputs:
      - src/hooks/use-rag-outreach.ts
      - src/hooks/use-url-validator.ts
      - src/components/LiveEventLog.tsx
      - src/components/CommandCenterEnhanced.tsx
      - src/app/schemes/page.tsx
      - src/app/funding/page.tsx
      - src/app/jobs/page.tsx
      - src/app/command-center/page.tsx
    nexus_skill: "react-query-api-layer"
    llm: "Kimi K2.6"
    estimated_tokens: 15000

  - id: "phase-10-testing"
    type: test
    name: "E2E + Integration Testing"
    inputs: ["phase-9"]
    outputs:
      - tests/e2e/rag-outreach.spec.ts
      - tests/e2e/sse-live-feed.spec.ts
      - tests/e2e/gov-schemes.spec.ts
      - tests/e2e/funding-detection.spec.ts
      - tests/e2e/job-intelligence.spec.ts
      - tests/e2e/url-validation.spec.ts
    nexus_skill: "e2e-testing"
    llm: "Kimi K2.6"
    estimated_tokens: 10000

  - id: "phase-11-deploy"
    type: deploy
    name: "Production Deployment"
    inputs: ["phase-10"]
    outputs:
      - .github/workflows/deploy.yml
      - railway.toml
      - vercel.json
      - infra/docker-compose.prod.yml
    nexus_skill: "land-and-deploy"
    llm: "Kimi K2.6"
    estimated_tokens: 5000

  - id: "phase-12-audit"
    type: audit
    name: "Final Verification"
    inputs: ["phase-11"]
    outputs:
      - AUDIT_REPORT.md
      - HEALTH_REPORT.md
      - PERFORMANCE_BENCHMARK.md
    nexus_skill: "qa"
    llm: "Kimi K2.6"
    estimated_tokens: 5000
```

---

## 6. Deployment: Vercel + Railway + Supabase

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LeadIQ Production Deploy                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   Vercel    │───▶│   Railway    │───▶│  Supabase    │     │
│  │  (Frontend) │    │  (Backend)   │    │  (Database)  │     │
│  │   Next.js   │    │   FastAPI    │    │ PostgreSQL   │     │
│  │   $0/month  │    │   $5/month   │    │  + pgvector  │     │
│  └─────────────┘    └──────┬───────┘    │   $0/month   │     │
│                            │             └──────────────┘     │
│                            │                                  │
│                            ▼                                  │
│                     ┌──────────────┐                         │
│                     │   Redis      │                         │
│                     │   Upstash    │                         │
│                     │   $0/month   │                         │
│                     │  (30MB free) │                         │
│                     └──────────────┘                         │
│                                                              │
│  LLM APIs (Free Tier):                                      │
│  • NVIDIA NIM → DeepSeek/Llama/Mistral                      │
│  • Gemini Flash → 60 RPM, 24/7                               │
│  • Kimi K2.6 → OpenCode (current session)                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Minimum Resource Requirements

| Component | Provider | Plan | Cost | Why |
|-----------|----------|------|------|-----|
| **Frontend** | Vercel | Hobby (free) | $0 | Next.js 15, serverless |
| **Backend** | Railway | Starter | $5/mo | FastAPI, always-on |
| **Database** | Supabase | Free tier | $0 | PostgreSQL + pgvector |
| **Redis** | Upstash | Free tier | $0 | 30MB, 10K commands/day |
| **LLM** | NVIDIA NIM | Free tier | $0 | 1,000-5,000 req/month |
| **LLM Backup** | Gemini | GCP trial | $0 | 60 RPM, 3 months |
| **Storage** | Supabase | Free tier | $0 | 1GB |
| **Domain** | Cloudflare | Free | $0 | DNS + SSL |
| **Monitoring** | Sentry | Developer | $0 | 5K errors/month |
| **Total** | — | — | **$5/month** | Minimum production |

### Database Schema (pgvector)

```sql
-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Company context for RAG
CREATE TABLE company_context (
    id SERIAL PRIMARY KEY,
    company_id VARCHAR(255) NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(384),  -- all-MiniLM-L6-v2
    source_type VARCHAR(50),
    source_url VARCHAR(500),
    trust_score FLOAT DEFAULT 5.0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_company_context_company ON company_context(company_id);
CREATE INDEX idx_company_context_embedding ON company_context 
USING hnsw (embedding vector_cosine_ops);

-- Government schemes
CREATE TABLE gov_schemes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    eligibility TEXT,
    deadline DATE,
    funding_amount VARCHAR(100),
    source_url VARCHAR(500),
    trust_score FLOAT DEFAULT 10.0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Funding events
CREATE TABLE funding_events (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255),
    amount VARCHAR(100),
    round_type VARCHAR(50),
    investors TEXT[],
    source_url VARCHAR(500),
    trust_score FLOAT DEFAULT 7.0,
    announced_at DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Job signals
CREATE TABLE job_signals (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255),
    role VARCHAR(255),
    skills TEXT[],
    location VARCHAR(255),
    salary_range VARCHAR(100),
    hiring_velocity INT,  -- 1-10
    source_url VARCHAR(500),
    posted_at DATE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Environment Variables

```bash
# .env.production
# Frontend
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
NEXT_PUBLIC_APP_NAME=LeadIQ
NEXT_PUBLIC_APP_VERSION=2.0.0

# Backend
DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres
REDIS_URL=rediss://default:[password]@[host]:[port]
SECRET_KEY=your-secret-key
API_RATE_LIMIT=100/minute

# LLM APIs
NVIDIA_API_KEY=nvapi-xxx  # NVIDIA NIM free tier
GEMINI_API_KEY=AIxxx      # GCP 3-month trial
OPENAI_API_KEY=sk-xxx     # Optional

# Monitoring
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
LOG_LEVEL=info
```

### Deployment Steps

```bash
# Step 1: Database Setup
supabase link --project-ref your-project-ref
supabase db push

# Step 2: Backend Deploy
railway login
railway up

# Step 3: Frontend Deploy
vercel --prod

# Step 4: Verify
curl https://your-backend.up.railway.app/api/health
curl https://your-frontend.vercel.app/api/health
```

### Health Check Endpoints

| Endpoint | Expected Response |
|----------|-------------------|
| `GET /api/health` | `{"status":"ok"}` |
| `GET /api/stream/health` | `{"redis":"connected"}` |
| `GET /api/auth/me` | `{"authenticated":true}` |
| `GET /api/leads` | `{"leads":[],"total":0}` |

---

## 7. Communication Tunnel (Frontend ↔ Backend)

### REST API Proxy

```typescript
// src/app/api/proxy/route.ts
export const config = { runtime: 'edge' };

export default async function handler(req: NextRequest) {
  const { pathname, search } = new URL(req.url);
  const backendUrl = `${process.env.NEXT_PUBLIC_API_URL}${pathname.replace('/api/proxy', '/api')}${search}`;
  
  const res = await fetch(backendUrl, {
    method: req.method,
    headers: { ...req.headers, host: undefined },
    body: req.body,
  });
  
  return new NextResponse(res.body, { status: res.status, headers: res.headers });
}
```

### Data Flow Example

```
User clicks "Generate Outreach"
    │
    ▼
React Query: useRagOutreach.mutate({ companyId, prompt })
    │
    ▼
POST /api/proxy/api/outreach/rag (Next.js API route)
    │
    ▼
Proxy to FastAPI: POST /api/outreach/rag
    │
    ▼
Backend: outreach_rag.py
  ├─ Step 1: Retrieve context from pgvector (top-k=5)
  ├─ Step 2: Build prompt with RAG context
  ├─ Step 3: Call LLM via multi-LLM router
  │    ├─ NVIDIA NIM (DeepSeek) for reasoning
  │    └─ Gemini for generation (fallback)
  ├─ Step 4: Validate output
  └─ Step 5: Return personalized outreach
    │
    ▼
Return: { outreach: "...", sources: [...], trustScores: [...] }
    │
    ▼
Frontend: Display outreach + trust badges + source citations
```

---

## 8. Cost Analysis

| Resource | Monthly Cost | Limits |
|----------|-------------|--------|
| Vercel Hobby | $0 | 100GB bandwidth, 10s serverless functions |
| Railway Starter | $5 | 512MB RAM, 1vCPU, always-on |
| Supabase Free | $0 | 500MB DB, 2GB bandwidth, 100K API calls |
| Upstash Free | $0 | 30MB, 10K commands/day |
| NVIDIA NIM Free | $0 | 1,000-5,000 requests/month |
| Gemini GCP Trial | $0 | 60 RPM, 3 months |
| Sentry Developer | $0 | 5K errors/month |
| **Total** | **$5/month** | Full production stack |

---

## 9. Execution Approval

**Type "execute" or "go" to begin Phase 1 (RAG Core Implementation).**

**Phases will execute in order:**
1. P0 (Week 1): RAG + Multi-LLM + URL Validator
2. P1 (Week 2): Gov Scraper + Funding Detector + Job Intelligence
3. P2 (Week 3): Advanced NLP + ML Scoring Stack
4. P3 (Week 4): Frontend Integration + Testing + Deploy + Audit

**Estimated Total:** 4-6 weeks, 500K tokens, $5/month infrastructure cost.

---

*Plan Version: 1.0 | Generated: 2026-05-11 | Status: READY FOR EXECUTION*

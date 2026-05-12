# LeadIQ Master Implementation Plan
> Research-Driven, Adaptive-Imagining-Cat Execution
> Complete transformation for Indian Market Domination
> Version: 1.0 | Date: 2026-05-11

---

## TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [Research Foundation](#research-foundation)
3. [Architecture Overview](#architecture-overview)
4. [Phase Implementation Details](#phase-implementation-details)
5. [Platform Catalog](#platform-catalog)
6. [Execution Orchestration](#execution-orchestration)
7. [Metrics & Verification](#metrics--verification)
8. [Risk Analysis](#risk-analysis)
9. [Appendix](#appendix)

---

## EXECUTIVE SUMMARY

### Current State
- **Existing Collectors:** Reddit, HN, Twitter, GitHub, StackOverflow, Telegram, RSS, ProductHunt
- **Government Sources:** DPIIT (partial), MCA21 (placeholder)
- **Job Platforms:** NONE
- **Scoring:** Heuristic + LLM fallback (not optimal)
- **Daily Volume:** ~500 leads/day
- **Accuracy:** ~60%

### Target State
- **New Collectors:** 15+ job platforms, 5 government sources
- **Scoring:** Gradient Boosting (98.39% accuracy) + LLM hybrid
- **Daily Volume:** 25,000+ leads/day
- **Accuracy:** >90%
- **Conversion Rate:** >15% (from 5%)

### Investment Required
- **Time:** 12 weeks (3 months)
- **Team:** 4-5 engineers
- **Infrastructure:** Proxy service, GPU for ML
- **Expected ROI:** $634K+ annual lead pipeline value

---

## RESEARCH FOUNDATION

### Papers Analyzed (15+)

| Paper | Key Metric | Impact |
|-------|------------|--------|
| SalesRLAgent (arXiv 2503.23303) | 96.7% accuracy, 43.2% conversion boost | RL scoring layer |
| Gradient Boosting (Frontiers 2025) | 98.39% accuracy | Core scoring model |
| VALOR (arXiv 2604.02472) | 2.7x revenue increase | Uplift modeling |
| CPOG (LinkedIn 2025) | Production validated | Pipeline architecture |
| Geo-DANN (ICLR 2026) | 4.3% AUPR gain, 12.3% geo-fairness | India-state fairness |
| asLLR (arXiv 2510.21713) | 9.5% sales volume increase | LLM qualitative layer |
| Scrapus (Frontiers 2025) | 3x lead yield, 90% precision/recall | Scraping optimization |

### Research Synthesis

```
Optimal Scoring Architecture:
├── GBM (30%) - Tabular feature prediction
├── LLM (25%) - Text qualitative analysis
├── RL (20%) - Sequential decision optimization
├── Uplift (15%) - Revenue-aware ranking
└── Geo (10%) - Geography fairness adjustment

Expected Accuracy: >85%
Expected Lift: 3-5x over current heuristic
```

---

## ARCHITECTURE OVERVIEW

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA COLLECTION                           │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ JOB PLATFORMS│  │ GOVT SOURCES │  │   SOCIAL/EXISTING       │  │
│  │              │  │              │  │                         │  │
│  │ • Naukri     │  │ • DPIIT v2   │  │ • Reddit               │  │
│  │ • Internshala│  │ • MCA21      │  │ • HN                   │  │
│  │ • LinkedIn   │  │ • GeM        │  │ • GitHub               │  │
│  │ • Indeed     │  │ • MSME       │  │ • StackOverflow        │  │
│  │ • Shine      │  │ • API Setu   │  │ • Telegram             │  │
│  │ • Monster    │  │              │  │ • Twitter              │  │
│  │ • +8 more    │  │              │  │ • ProductHunt          │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬────────────┘  │
│         │                  │                      │                │
│         └──────────────────┼──────────────────────┘                │
│                            │                                       │
│                            ▼                                       │
│                  ┌─────────────────────┐                            │
│                  │   REDIS STREAMS     │                            │
│                  │                     │                            │
│                  │ lead:govt_collected │                            │
│                  │ lead:jobs_collected │                            │
│                  │ lead:social_collected│                           │
│                  └──────────┬──────────┘                            │
│                             │                                      │
└─────────────────────────────┼──────────────────────────────────────┘
                              │
┌─────────────────────────────┼──────────────────────────────────────┐
│                             ▼                                      │
│                    ┌─────────────────────┐                         │
│                    │   ENRICHMENT LAYER   │                         │
│                    │                      │                         │
│                    │ • Email finder       │                         │
│                    │ • Phone enrichment   │                         │
│                    │ • Govt cross-ref     │                         │
│                    │ • Company verify     │                         │
│                    └──────────┬───────────┘                         │
│                               │                                    │
│                               ▼                                    │
│                    ┌─────────────────────┐                         │
│                    │   SCORING ENGINE     │                        │
│                    │                      │                        │
│                    │ ┌───────────────┐   │                        │
│                    │ │  GBM (30%)   │   │                        │
│                    │ │  LLM (25%)   │   │                        │
│                    │ │  RL (20%)    │   │                        │
│                    │ │  Uplift (15%)│   │                        │
│                    │ │  Geo (10%)   │   │                        │
│                    │ └───────────────┘   │                        │
│                    │         │           │                        │
│                    │         ▼           │                        │
│                    │  Composite Score    │                        │
│                    └──────────┬──────────┘                        │
│                               │                                    │
│                               ▼                                    │
│                    ┌─────────────────────┐                         │
│                    │   RANKING LAYER      │                        │
│                    │                      │                        │
│                    │ Hot (≥75)  → Immediate outreach              │
│                    │ Warm (50-74) → Nurture sequence                │
│                    │ Cool (25-49) → Long-term nurture               │
│                    │ Cold (<25) → Drip campaign                    │
│                    └──────────┬──────────┘                        │
│                               │                                    │
│                               ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                      API LAYER                                │  │
│  │                                                               │  │
│  │  /api/collect/*    /api/leads/*    /api/scoring/*            │  │
│  │  /api/analytics/*  /api/admin/*    /api/health                │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                   POSTGRESQL + PGVECTOR                        │  │
│  │                                                               │  │
│  │  posts    leads    feedback    quota_usage    user_profiles   │  │
│  └─────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## PHASE IMPLEMENTATION DETAILS

### Phase 1: Foundation (Week 1)
**Goal:** Production-grade scraping infrastructure

**Files Created:**
- `backend/collectors/scraping_utils.py`
- `backend/collectors/proxy_manager.py`
- `backend/collectors/stealth_session.py`
- `backend/collectors/retry_handler.py`

**Dependencies Added:**
```txt
playwright>=1.40.0
playwright-stealth>=1.0.0
curl_cffi>=0.6.0
fake-useragent>=1.4.0
tenacity>=8.2.0
```

**Verification:**
- Bot detection pass rate >95% (bot.sannysoft.com)
- Proxy rotation success >90%
- Retry success >95%

---

### Phase 2-3: Job Platform Collectors (Week 2-3)
**Goal:** Deploy Naukri + Internshala scrapers

**Naukri Strategy:**
- API interception via Playwright + stealth
- Residential proxy rotation every 20 requests
- 3-5 second delays between requests
- Fallback HTML parsing

**Internshala Strategy:**
- Direct HTML parsing with stealth headers
- curl_cffi for TLS fingerprint bypass
- Pagination handling

**Expected Output:** 60,000+ jobs/day

---

### Phase 4-5: Government APIs + More Platforms (Week 4-5)
**Goal:** Integrate government sources + additional job platforms

**Government Sources:**
- DPIIT v2 (enhanced fields)
- MCA21 (company details)
- GeM Portal (vendor profiles)
- MSME Udyam (registration data)
- API Setu (4,200+ APIs)

**Additional Platforms:**
- LinkedIn India Jobs
- Indeed India
- Shine.com
- Monster India
- +8 more niche platforms

**Expected Output:** 8,000+ leads/day (govt) + 5,000+ (additional)

---

### Phase 6-7: ML Scoring Engine (Week 6-7)
**Goal:** Research-backed scoring system

**Gradient Boosting (Phase 6):**
- 25 engineered features
- 200 estimators, max_depth=6
- ROC AUC target: >0.85

**LLM Hybrid (Phase 7):**
- Qualitative analysis via Gemini
- Buying signals + objection risks
- Composite weighting

**Expected Accuracy:** >85%

---

### Phase 8: Pipeline Integration (Week 8)
**Goal:** Connect all components

**Redis Streams:**
- `lead:govt_collected`
- `lead:jobs_collected`
- `lead:enriched`
- `lead:scored`

**API Endpoints:**
- `POST /api/collect/naukri`
- `POST /api/collect/internshala`
- `GET /api/leads/government`
- `GET /api/leads/jobs`
- `POST /api/scoring/batch`

---

### Phase 9-10: Performance + Quality (Week 9-10)
**Goal:** Scale and verify

**Performance Targets:**
- 25,000+ leads/day
- Pipeline latency <5 min
- Memory usage <2GB

**Quality Targets:**
- 90%+ data accuracy
- <10% false positives
- Real-time freshness

---

### Phase 11-12: Testing + Deployment (Week 11-12)
**Goal:** Production readiness

**Testing:**
- 80%+ unit test coverage
- Integration tests
- Load tests (1000+ req/s)

**Deployment:**
- Docker compose
- CI/CD pipeline
- Monitoring dashboard

---

## PLATFORM CATALOG

### Complete Platform List

| # | Platform | URL | Type | Volume/Day | Protection | Approach |
|---|----------|-----|------|-----------|------------|----------|
| 1 | **Naukri.com** | https://www.naukri.com/ | Jobs | 50,000 | HIGH | API interception + stealth |
| 2 | **Internshala** | https://internshala.com/ | Internships | 10,000 | MEDIUM | Direct parsing |
| 3 | **LinkedIn India** | https://www.linkedin.com/jobs/ | Jobs | 20,000 | HIGH | API + stealth |
| 4 | **Indeed India** | https://www.indeed.co.in/ | Jobs | 15,000 | MEDIUM | RSS + API |
| 5 | **Shine.com** | https://www.shine.com/ | Jobs | 5,000 | MEDIUM | Direct scraping |
| 6 | **Monster India** | https://www.monsterindia.com/ | Jobs | 3,000 | MEDIUM | Direct scraping |
| 7 | **Freshersworld** | https://www.freshersworld.com/ | Freshers | 2,000 | LOW | Direct parsing |
| 8 | **Hirist** | https://www.hirist.com/ | Tech | 2,000 | MEDIUM | Direct scraping |
| 9 | **CutShort** | https://cutshort.io/ | Startup | 1,500 | MEDIUM | API + stealth |
| 10 | **AngelList India** | https://wellfound.com/ | Startup | 1,000 | MEDIUM | Direct scraping |
| 11 | **Instahyre** | https://www.instahyre.com/ | Premium | 1,000 | MEDIUM | Direct scraping |
| 12 | **IIM Jobs** | https://www.iimjobs.com/ | Management | 500 | MEDIUM | Direct scraping |
| 13 | **Sarkari Result** | https://www.sarkariresult.com/ | Govt | 500 | LOW | Direct parsing |
| 14 | **FreeJobAlert** | https://www.freejobalert.com/ | Mixed | 300 | LOW | Direct parsing |
| 15 | **Employment News** | https://employmentnews.gov.in/ | Official | 100 | LOW | RSS |
| 16 | **DPIIT Registry** | https://startupindia.gov.in/ | Govt | 500 | LOW | Official API |
| 17 | **MCA21** | https://www.mca.gov.in/ | Corporate | 800 | MEDIUM | Direct scraping |
| 18 | **GeM Portal** | https://gem.gov.in/ | Govt Vendor | 1,000 | LOW | Official API |
| 19 | **MSME Udyam** | https://udyamregistration.gov.in/ | MSME | 2,000 | LOW | Official API |
| 20 | **API Setu** | https://apisetu.gov.in/ | Gateway | 4,200 APIs | LOW | Official API |

**Total Platforms:** 20
**Total Expected Volume:** 115,000+ jobs/day + 4,300 govt/day
**After Deduplication:** ~25,000 unique leads/day

---

## EXECUTION ORCHESTRATION

### Parallel Execution Groups

```
Group 1: Phase 1 (Week 1)
└── Foundation

Group 2: Phase 2 + Phase 3 + Phase 4 start (Week 2-3)
├── Naukri
├── Internshala
└── Government APIs (start)

Group 3: Phase 4 cont + Phase 5 (Week 4-5)
├── Government APIs (completion)
└── LinkedIn + Others

Group 4: Phase 6 (Week 6)
└── GBM Scoring

Group 5: Phase 7 + Phase 8 (Week 7-8)
├── LLM Scoring
└── Pipeline Integration

Group 6: Phase 9 + Phase 10 (Week 9-10)
├── Performance Optimization
└── Data Quality

Group 7: Phase 11 + Phase 12 (Week 11-12)
├── Testing
└── Deployment
```

### Critical Path

```
Phase 1 → Phase 2/3 → Phase 4/5 → Phase 6 → Phase 7 → Phase 8 → Phase 9/10 → Phase 11 → Phase 12

Critical Path Length: 12 weeks
```

---

## METRICS & VERIFICATION

### Phase Verification Checkpoints

| Phase | Key Metric | Target | Verification Method |
|-------|-----------|--------|---------------------|
| 1 | Bot detection pass | >95% | bot.sannysoft.com |
| 2 | Naukri extraction | 1000+ jobs | Count verification |
| 3 | Internshala extraction | 500+ internships | Count verification |
| 4 | Government leads | 3000+ | Count + field verification |
| 5 | Additional platforms | 5000+ | Count verification |
| 6 | GBM ROC AUC | >0.85 | Test set evaluation |
| 7 | LLM score range | 0-100 | Output validation |
| 8 | End-to-end flow | Working | Manual test |
| 9 | Daily volume | 25,000+ | Pipeline dashboard |
| 10 | Data accuracy | >90% | Sampling |
| 11 | Test coverage | >80% | Coverage report |
| 12 | Production ready | Yes | Checklist |

### Success Metrics Dashboard

```
Daily KPIs:
├── Leads collected: 25,000+
├── Government leads: 3,000+
├── Job leads: 15,000+
├── Social leads: 7,000+
├── Scoring accuracy: >85%
├── Pipeline latency: <5 min
└── False positive rate: <10%

Weekly KPIs:
├── Model retraining: Completed
├── Feature importance: Reviewed
├── Data quality: Audited
└── Conversion rate: Tracked

Monthly KPIs:
├── ROI calculation: Updated
├── Architecture review: Completed
├── Risk assessment: Updated
└── Team retrospective: Held
```

---

## RISK ANALYSIS

### Risk Matrix

| Risk | Impact | Probability | Score | Mitigation |
|------|--------|-------------|-------|------------|
| Naukri blocks scraper | HIGH | HIGH | 9 | Residential proxies, stealth, fallback HTML |
| Government API changes | MEDIUM | MEDIUM | 4 | Version pinning, fallback scraping |
| Model accuracy low | HIGH | LOW | 3 | Feature engineering, hyperparameter tuning |
| Memory issues at scale | MEDIUM | MEDIUM | 4 | Batch processing, horizontal scaling |
| Data quality issues | HIGH | MEDIUM | 6 | Validation pipeline, manual review |
| Team member unavailable | MEDIUM | LOW | 2 | Cross-training, contractors |
| Budget overrun | HIGH | LOW | 3 | Weekly tracking, scope management |
| Legal/ToS issues | HIGH | LOW | 3 | Compliance registry, legal review |

### Contingency Plans

**If Naukri blocks:**
1. Switch to HTML fallback
2. Increase proxy rotation frequency
3. Add more residential proxies
4. Reduce request rate further

**If GBM accuracy <0.85:**
1. Add more features
2. Try XGBoost or LightGBM
3. Increase training data
4. Feature selection optimization

**If pipeline can't scale:**
1. Add Celery workers
2. Implement batch processing
3. Add caching layer
4. Database optimization

---

## APPENDIX

### A. File Structure

```
plans/
├── research/
│   ├── RESEARCH_INDEX.md          # All papers summary
│   └── papers/
│       ├── sales_rl_agent.md      # arXiv 2503.23303
│       ├── gradient_boosting.md   # Frontiers 2025
│       ├── valor_uplift.md        # arXiv 2604.02472
│       ├── cpog_framework.md      # LinkedIn 2025
│       ├── geo_dann.md            # ICLR 2026
│       ├── asllr_llm.md           # arXiv 2510.21713
│       └── scrapus_ai.md          # Frontiers 2025
│
├── architecture/
│   ├── ARCHITECTURE_MASTER.md     # System design
│   ├── COLLECTORS_DESIGN.md      # Collector patterns
│   ├── SCORING_DESIGN.md         # ML architecture
│   └── PIPELINE_DESIGN.md        # Data flow
│
├── phases/
│   ├── PHASE_01_FOUNDATION.md    # Week 1
│   ├── PHASE_02_03_COLLECTORS.md # Week 2-3
│   ├── PHASE_04_05_GOVERNMENT.md # Week 4-5
│   ├── PHASE_06_07_ML_SCORING.md # Week 6-7
│   ├── PHASE_08_INTEGRATION.md   # Week 8
│   ├── PHASE_09_10_OPTIMIZATION.md # Week 9-10
│   └── PHASE_11_12_DEPLOYMENT.md # Week 11-12
│
├── execution/
│   ├── EXECUTION_ORCHESTRATION.md # DAG + timeline
│   ├── RESOURCE_ALLOCATION.md    # Team assignments
│   └── SCHEDULE.md               # Calendar
│
├── metrics/
│   ├── KPI_DASHBOARD.md          # Metrics definitions
│   ├── VERIFICATION_CHECKLIST.md # Per-phase checks
│   └── SUCCESS_CRITERIA.md       # Pass/fail criteria
│
└── platforms/
    ├── JOB_PLATFORMS.md          # All job sites
    ├── GOVERNMENT_APIS.md        # Govt sources
    └── COMPLIANCE_REGISTRY.md    # ToS tracking
```

### B. Technology Stack

```
Backend:
├── FastAPI 0.115+
├── SQLAlchemy 2.0+
├── AsyncPG 0.29+
├── Celery 5.4+
├── Redis 7+
└── PostgreSQL 16 + PGVector

Scraping:
├── Playwright 1.40+
├── Playwright-Stealth
├── curl_cffi 0.6+
├── Fake-UserAgent 1.4+
├── Scrapling 0.2+
└── BeautifulSoup 4.12+

Machine Learning:
├── Scikit-Learn 1.4+
├── XGBoost 2.0+
├── LightGBM 4.0+
├── Optuna 3.4+
├── Pandas 2.0+
└── NumPy 1.24+

LLM:
├── Google Generative AI 0.8+
├── LangExtract 0.1+
└── Prompt Versioning

Infrastructure:
├── Docker + Docker Compose
├── GitHub Actions CI/CD
├── Sentry Monitoring
└── StructLog + OpenTelemetry
```

### C. Compliance Registry

```
Source          Risk Level    Scraping    API        Retention
─────────────────────────────────────────────────────────────────
naukri          MEDIUM        Yes         No         30 days
internshala     LOW           Yes         No         30 days
linkedin        HIGH          Restricted  Yes        7 days
indeed          MEDIUM        Yes         No         30 days
shine           MEDIUM        Yes         No         30 days
monster         MEDIUM        Yes         No         30 days
freshersworld   LOW           Yes         No         30 days
hirist          MEDIUM        Yes         No         30 days
dpiit           LOW           Yes         Yes        90 days
mca21           LOW           Yes         Yes        90 days
gem             LOW           Yes         Yes        90 days
msme            LOW           Yes         Yes        90 days
reddit          MEDIUM        Yes         Yes        30 days
hn              LOW           Yes         Yes        90 days
github          LOW           Yes         Yes        90 days
```

### D. Contact & References

**Research Papers:**
- SalesRLAgent: arXiv:2503.23303
- Gradient Boosting: Frontiers 2025, DOI: 10.3389/frai.2025.1554325
- VALOR: arXiv:2604.02472
- CPOG: arXiv:2505.09847
- Geo-DANN: OpenReview ICLR 2026
- asLLR: arXiv:2510.21713
- Scrapus: Frontiers 2025, DOI: 10.3389/frai.2025.1606431

**Government APIs:**
- API Setu: https://apisetu.gov.in/
- DPIIT: https://api.startupindia.gov.in/
- MCA21: https://www.mca.gov.in/
- GeM: https://gem.gov.in/
- MSME: https://udyamregistration.gov.in/

**Platform URLs:**
- See PLATFORM_CATALOG.md for complete list

---

*Master Implementation Plan*
*Version: 1.0*
*Date: 2026-05-11*
*Research Papers: 15+*
*Platforms: 20*
*Implementation Phases: 12*
*Expected Duration: 12 weeks*
*Expected ROI: $634K+/year*

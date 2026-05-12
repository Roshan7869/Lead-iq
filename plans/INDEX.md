# LeadIQ Implementation Plan - Complete Index
> Master index for all plan documents
> Adaptive-Imagining-Cat execution system
> Date: 2026-05-11

---

## PLAN STRUCTURE

```
plans/
├── INDEX.md                          # This file
├── MASTER_IMPLEMENTATION_PLAN.md     # Complete master plan
├── AUDIT_OPTIMIZATION_PLAN.md        # Original audit (root)
│
├── research/
│   ├── RESEARCH_INDEX.md             # All 15+ papers indexed
│   └── papers/                       # Individual paper summaries
│
├── architecture/
│   └── ARCHITECTURE_MASTER.md        # System design docs
│
├── phases/
│   ├── PHASE_01_FOUNDATION.md      # Week 1: Scraping infrastructure
│   ├── PHASE_02_03_COLLECTORS.md   # Week 2-3: Naukri + Internshala
│   ├── PHASE_04_05_GOVERNMENT.md   # Week 4-5: Govt APIs
│   ├── PHASE_06_07_ML_SCORING.md   # Week 6-7: ML scoring engine
│   ├── PHASE_08_INTEGRATION.md     # Week 8: Pipeline integration
│   ├── PHASE_09_10_OPTIMIZATION.md # Week 9-10: Performance + Quality
│   └── PHASE_11_12_DEPLOYMENT.md   # Week 11-12: Testing + Deployment
│
├── execution/
│   └── EXECUTION_ORCHESTRATION.md   # DAG + timeline + resources
│
├── metrics/
│   └── KPI_DASHBOARD.md            # Baseline vs Target metrics
│
└── platforms/
    ├── PLATFORM_CATALOG.md          # All 29 platforms with URLs
    └── COMPLIANCE_REGISTRY.md       # ToS compliance for all sources
```

---

## QUICK REFERENCE

### Research Papers (7 Core + 8 Supporting)
| # | Paper | Key Metric | File |
|---|-------|------------|------|
| 1 | SalesRLAgent (arXiv 2503.23303) | 96.7% accuracy | `plans/research/RESEARCH_INDEX.md` |
| 2 | Gradient Boosting (Frontiers 2025) | 98.39% accuracy | `plans/research/RESEARCH_INDEX.md` |
| 3 | VALOR (arXiv 2604.02472) | 2.7x revenue | `plans/research/RESEARCH_INDEX.md` |
| 4 | CPOG (LinkedIn 2025) | Production validated | `plans/research/RESEARCH_INDEX.md` |
| 5 | Geo-DANN (ICLR 2026) | 4.3% AUPR gain | `plans/research/RESEARCH_INDEX.md` |
| 6 | asLLR (arXiv 2510.21713) | 9.5% sales increase | `plans/research/RESEARCH_INDEX.md` |
| 7 | Scrapus (Frontiers 2025) | 3x yield, 90% precision | `plans/research/RESEARCH_INDEX.md` |

### Implementation Phases (12 Weeks)
| Phase | Duration | Focus | Document |
|-------|----------|-------|----------|
| 1 | Week 1 | Foundation | `phases/PHASE_01_FOUNDATION.md` |
| 2 | Week 2 | Naukri | `phases/PHASE_02_03_COLLECTORS.md` |
| 3 | Week 2-3 | Internshala | `phases/PHASE_02_03_COLLECTORS.md` |
| 4 | Week 4-5 | Government APIs | `phases/PHASE_04_05_GOVERNMENT.md` |
| 5 | Week 5 | LinkedIn + Others | `phases/PHASE_04_05_GOVERNMENT.md` |
| 6 | Week 6 | GBM Scoring | `phases/PHASE_06_07_ML_SCORING.md` |
| 7 | Week 7 | LLM Scoring | `phases/PHASE_06_07_ML_SCORING.md` |
| 8 | Week 8 | Integration | `phases/PHASE_08_INTEGRATION.md` |
| 9 | Week 9 | Performance | `phases/PHASE_09_10_OPTIMIZATION.md` |
| 10 | Week 10 | Quality | `phases/PHASE_09_10_OPTIMIZATION.md` |
| 11 | Week 11 | Testing | `phases/PHASE_11_12_DEPLOYMENT.md` |
| 12 | Week 12 | Deployment | `phases/PHASE_11_12_DEPLOYMENT.md` |

### Platforms (29 Total)
| Tier | Count | Platforms | Document |
|------|-------|-----------|----------|
| 1 - Critical | 3 | Naukri, Internshala, LinkedIn | `platforms/PLATFORM_CATALOG.md` |
| 2 - High Value | 4 | Indeed, Shine, Monster, NaukriGulf | `platforms/PLATFORM_CATALOG.md` |
| 3 - Niche | 6 | Freshersworld, Hirist, CutShort, etc. | `platforms/PLATFORM_CATALOG.md` |
| 4 - Government | 5 | DPIIT, MCA21, GeM, MSME, API Setu | `platforms/PLATFORM_CATALOG.md` |
| 5 - Govt Jobs | 3 | Sarkari Result, FreeJobAlert, Employment News | `platforms/PLATFORM_CATALOG.md` |
| 6 - Social | 8 | Reddit, HN, GitHub, etc. | `platforms/PLATFORM_CATALOG.md` |

---

## KEY METRICS

| Metric | Baseline | Target | Improvement |
|--------|----------|--------|-------------|
| Daily Leads | 500 | 25,000+ | 50x |
| Accuracy | 60% | >90% | +30pp |
| Conversion Rate | 5% | >15% | +10pp |
| Scoring Accuracy | Heuristic | >85% ML | New |
| Sources | 8 | 29 | +21 |
| Govt Sources | 1 | 5 | +4 |
| Job Platforms | 0 | 15 | +15 |

---

## EXECUTION STATUS

```
Phase 0: ✅ State Preservation    (Research saved to plans/)
Phase 1: ⏳ Foundation            (Week 1 - Pending)
Phase 2: ⏳ Naukri                (Week 2 - Pending)
Phase 3: ⏳ Internshala           (Week 2-3 - Pending)
Phase 4: ⏳ Government APIs       (Week 4-5 - Pending)
Phase 5: ⏳ LinkedIn + Others     (Week 5 - Pending)
Phase 6: ⏳ GBM Scoring           (Week 6 - Pending)
Phase 7: ⏳ LLM Scoring           (Week 7 - Pending)
Phase 8: ⏳ Integration           (Week 8 - Pending)
Phase 9: ⏳ Performance           (Week 9 - Pending)
Phase 10: ⏳ Quality              (Week 10 - Pending)
Phase 11: ⏳ Testing              (Week 11 - Pending)
Phase 12: ⏳ Deployment           (Week 12 - Pending)
```

---

## NEXT STEPS

1. **Start Phase 1** - Install dependencies, build scraping infrastructure
2. **Register API Setu** - Get API key for government data access
3. **Setup Proxy Service** - Configure residential proxy pool
4. **Review Architecture** - Team review of ARCHITECTURE_MASTER.md
5. **Plan Sprint 1** - Week 1 task breakdown and assignment

---

*Plan Index v1.0*
*Total Documents: 15*
*Total Platforms: 29*
*Research Papers: 15+*
*Implementation Phases: 12*
*Expected Duration: 12 weeks*

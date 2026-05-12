# KPI Dashboard & Success Metrics
> Comprehensive metrics for LeadIQ optimization
> Baseline vs Target tracking
> Date: 2026-05-11

---

## BASELINE METRICS (Current State)

### Collection Metrics
| Metric | Current | Unit |
|--------|---------|------|
| Daily leads collected | ~500 | leads/day |
| Sources active | 8 | platforms |
| Government sources | 1 (DPIIT partial) | platforms |
| Job platforms | 0 | platforms |
| Collection latency | ~10 | minutes |
| Data freshness | Daily | frequency |

### Quality Metrics
| Metric | Current | Unit |
|--------|---------|------|
| Lead accuracy | ~60% | percentage |
| False positive rate | ~40% | percentage |
| Duplicate rate | ~15% | percentage |
| Missing contact info | ~50% | percentage |
| Schema validation pass | ~70% | percentage |

### Scoring Metrics
| Metric | Current | Unit |
|--------|---------|------|
| Scoring method | Heuristic | type |
| Conversion prediction | N/A | N/A |
| Model accuracy | N/A | N/A |
| Feature count | 12 | features |
| Score range | 0-100 | points |
| Band distribution | 80% cold | percentage |

### Business Metrics
| Metric | Current | Unit |
|--------|---------|------|
| Conversion rate | ~5% | percentage |
| Sales team satisfaction | Low | qualitative |
| Time to first contact | 2-3 days | days |
| Pipeline velocity | Slow | qualitative |
| Cost per lead | $10-15 | USD |

---

## TARGET METRICS (After Optimization)

### Collection Metrics
| Metric | Target | Unit | Timeline |
|--------|--------|------|----------|
| Daily leads collected | 25,000+ | leads/day | Week 9 |
| Sources active | 29 | platforms | Week 5 |
| Government sources | 5 | platforms | Week 4 |
| Job platforms | 15 | platforms | Week 5 |
| Collection latency | <5 | minutes | Week 9 |
| Data freshness | Real-time | frequency | Week 10 |

### Quality Metrics
| Metric | Target | Unit | Timeline |
|--------|--------|------|----------|
| Lead accuracy | >90% | percentage | Week 10 |
| False positive rate | <10% | percentage | Week 10 |
| Duplicate rate | <5% | percentage | Week 8 |
| Missing contact info | <20% | percentage | Week 8 |
| Schema validation pass | >95% | percentage | Week 10 |

### Scoring Metrics
| Metric | Target | Unit | Timeline |
|--------|--------|------|----------|
| Scoring method | GBM+LLM Hybrid | type | Week 7 |
| ROC AUC | >0.85 | score | Week 6 |
| Model accuracy | >85% | percentage | Week 7 |
| Feature count | 25 | features | Week 6 |
| Score range | 0-100 | points | Week 6 |
| Band distribution | 20% hot, 30% warm | percentage | Week 7 |

### Business Metrics
| Metric | Target | Unit | Timeline |
|--------|--------|------|----------|
| Conversion rate | >15% | percentage | Week 12 |
| Sales team satisfaction | High | qualitative | Week 12 |
| Time to first contact | <1 day | days | Week 8 |
| Pipeline velocity | Fast | qualitative | Week 12 |
| Cost per lead | <$2 | USD | Week 9 |

---

## DAILY KPI DASHBOARD

### Morning Check (9 AM IST)
```
┌────────────────────────────────────────────────────────────┐
│ DAILY COLLECTION SUMMARY                                   │
├────────────────────────────────────────────────────────────┤
│ Total Leads:        25,847          ▲ +2,847 vs yesterday │
│ Govt Sources:       3,421           ▲ +421                │
│ Job Platforms:      15,203          ▲ +1,203              │
│ Social Sources:     7,223           ▲ +1,223              │
│                                                            │
│ Top Sources:                                               │
│ 1. Naukri:         8,542          (33% of job leads)      │
│ 2. DPIIT:          1,203          (35% of govt leads)     │
│ 3. LinkedIn:       4,102          (27% of job leads)      │
│ 4. MCA21:          892            (26% of govt leads)     │
│ 5. Reddit:         2,104          (29% of social)        │
│                                                            │
│ Quality Check:                                             │
│ Schema Valid:       24,203          (93.6% ✅)            │
│ With Contact:       21,445          (83.0% ✅)              │
│ Gov Verified:       3,089           (90.3% of govt ✅)      │
│ Duplicate Rate:     3.2%            ✅                    │
│                                                            │
│ Scoring:                                                   │
│ Hot Leads (≥75):   2,584           (10.0% 🟢)            │
│ Warm (50-74):     6,462           (25.0% 🟡)            │
│ Cool (25-49):     8,012           (31.0% 🟠)            │
│ Cold (<25):       8,789           (34.0% 🔴)            │
│                                                            │
│ Alert: 3 sources need attention                            │
└────────────────────────────────────────────────────────────┘
```

### Real-Time Monitoring
```
┌────────────────────────────────────────────────────────────┐
│ PIPELINE HEALTH                                            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ Collectors:          ✅ All 29 running                    │
│ Queue Depth:           142 jobs (normal)                   │
│ Processing Rate:       1,847 leads/hour                    │
│ Avg Latency:           2.3 minutes                         │
│ Error Rate:            0.8% (target: <2%)                 │
│                                                            │
│ Redis Streams:                                             │
│ lead:govt_collected    3,421 msgs    Lag: 12s ✅          │
│ lead:jobs_collected    15,203 msgs   Lag: 8s ✅           │
│ lead:enriched          22,104 msgs   Lag: 15s ✅           │
│ lead:scored            21,892 msgs   Lag: 23s ✅           │
│                                                            │
│ Database:                                                  │
│ Active Connections:    47/100 ✅                           │
│ Query Time (p95):      45ms ✅                             │
│ Disk Usage:            67% ✅                              │
│                                                            │
│ ML Model:                                                  │
│ GBM Loaded:            ✅                                  │
│ LLM API:               ✅ Latency: 1.2s                    │
│ Cache Hit Rate:        78%                                 │
│                                                            │
│ ⚠️  Alert: Naukri response time elevated (4.2s avg)       │
└────────────────────────────────────────────────────────────┘
```

---

## WEEKLY REVIEW METRICS

### Week 1: Foundation
- [ ] Dependencies installed: all 10 packages
- [ ] Stealth tests passing: >95%
- [ ] Proxy pool active: >50 proxies
- [ ] Retry logic working: >95% success
- [ ] Code review: approved

### Week 2-3: Job Collectors
- [ ] Naukri: 5,000+ jobs extracted
- [ ] Internshala: 2,000+ internships
- [ ] Salary parsing accuracy: >90%
- [ ] No IP bans: verified
- [ ] Data schema: validated

### Week 4-5: Government APIs
- [ ] DPIIT: 2,500+ startups
- [ ] MCA21: 500+ companies
- [ ] GeM: 500+ vendors
- [ ] MSME: 1,000+ registrations
- [ ] Cross-reference: 50%+ match rate

### Week 6: GBM Scoring
- [ ] Training data: 1,000+ leads
- [ ] ROC AUC: >0.85
- [ ] Feature importance: extracted
- [ ] Model saved: versioned
- [ ] A/B test: baseline vs new

### Week 7: LLM Scoring
- [ ] Qualitative scores: computed
- [ ] Composite scores: calculated
- [ ] Band distribution: reasonable
- [ ] Confidence scores: computed
- [ ] Sales feedback: positive

### Week 8: Integration
- [ ] Redis streams: all active
- [ ] API endpoints: responding
- [ ] Workers: processing
- [ ] Deduplication: <5%
- [ ] Enrichment: running

### Week 9-10: Performance + Quality
- [ ] Volume target: 25,000/day
- [ ] Latency target: <5 min
- [ ] Accuracy target: >90%
- [ ] Error rate: <2%
- [ ] Memory usage: <2GB

### Week 11-12: Testing + Deployment
- [ ] Test coverage: >80%
- [ ] All tests: passing
- [ ] Load test: >1000 req/s
- [ ] Production: deployed
- [ ] Monitoring: active

---

## METRIC CALCULATIONS

### Lead Accuracy
```python
def calculate_lead_accuracy(leads: List[Lead]) -> float:
    """Calculate lead accuracy percentage"""
    total = len(leads)
    if total == 0:
        return 0.0
        
    accurate = sum(1 for l in leads if is_accurate(l))
    return (accurate / total) * 100

def is_accurate(lead: Lead) -> bool:
    """Check if lead data is accurate"""
    checks = [
        lead.company_name is not None and len(lead.company_name) > 2,
        lead.title is not None and len(lead.title) > 5,
        lead.source in VALID_SOURCES,
        lead.collected_at is not None,
        lead.content_hash is not None,
    ]
    return all(checks)
```

### Duplicate Rate
```python
def calculate_duplicate_rate(leads: List[Lead]) -> float:
    """Calculate duplicate rate"""
    total = len(leads)
    if total == 0:
        return 0.0
        
    unique_hashes = set(l.content_hash for l in leads)
    duplicates = total - len(unique_hashes)
    return (duplicates / total) * 100
```

### Scoring Accuracy (ROC AUC)
```python
def calculate_roc_auc(y_true: List[bool], y_scores: List[float]) -> float:
    """Calculate ROC AUC for scoring model"""
    from sklearn.metrics import roc_auc_score
    return roc_auc_score(y_true, y_scores)
```

### Pipeline Latency
```python
def calculate_pipeline_latency(leads: List[Lead]) -> float:
    """Calculate average pipeline latency in minutes"""
    latencies = []
    for lead in leads:
        if lead.collected_at and lead.scored_at:
            latency = (lead.scored_at - lead.collected_at).total_seconds() / 60
            latencies.append(latency)
    
    return sum(latencies) / len(latencies) if latencies else 0
```

---

## ALERTING THRESHOLDS

### Critical Alerts (Immediate Action)
| Metric | Threshold | Action |
|--------|-----------|--------|
| Collector failure rate | >10% | Pause collector, investigate |
| Pipeline latency | >30 min | Scale workers, check bottlenecks |
| Database connections | >90% | Add connection pool, optimize queries |
| Error rate | >5% | Emergency rollback |
| Disk usage | >85% | Cleanup, add storage |

### Warning Alerts (Review Required)
| Metric | Threshold | Action |
|--------|-----------|--------|
| Collector failure rate | >5% | Review logs, tune configuration |
| Pipeline latency | >15 min | Monitor, plan scaling |
| Duplicate rate | >10% | Tune deduplication threshold |
| Missing contact info | >30% | Improve enrichment |
| Cache hit rate | <50% | Review cache strategy |

### Info Alerts (FYI)
| Metric | Threshold | Action |
|--------|-----------|--------|
| New source added | Any | Update documentation |
| Model retrained | Any | Review metrics |
| Volume spike | >150% normal | Investigate |
| Volume drop | <50% normal | Investigate |

---

## REPORTING TEMPLATES

### Daily Report
```
LeadIQ Daily Report - {date}
================================

COLLECTION
- Total leads: {total_leads}
- Government: {govt_leads}
- Jobs: {job_leads}
- Social: {social_leads}

QUALITY
- Accuracy: {accuracy}%
- Duplicates: {duplicate_rate}%
- Valid schema: {schema_valid}%

SCORING
- Hot leads: {hot_count} ({hot_pct}%)
- Warm leads: {warm_count} ({warm_pct}%)
- Average score: {avg_score}

PIPELINE
- Latency (p95): {latency_p95} min
- Error rate: {error_rate}%
- Queue depth: {queue_depth}

ALERTS
{alerts}
```

### Weekly Report
```
LeadIQ Weekly Report - {week}
================================

ACCOMPLISHMENTS
- {list of completed phases/tasks}

METRICS TREND
- Volume: {last_week} → {this_week} ({change}%)
- Accuracy: {last_week} → {this_week} ({change}%)
- Conversion: {last_week} → {this_week} ({change}%)

ISSUES
- {list of issues encountered}

PLANS
- {list of plans for next week}

RISKS
- {list of risks and mitigations}
```

### Monthly Report
```
LeadIQ Monthly Report - {month}
================================

EXECUTIVE SUMMARY
- Total leads collected: {total}
- Conversion rate: {conversion}%
- Revenue impact: ${revenue}

PHASE PROGRESS
- {phase completion status}

TECHNICAL METRICS
- Uptime: {uptime}%
- API response time (p95): {latency}ms
- Error rate: {error_rate}%

BUSINESS METRICS
- Leads per sales rep: {leads_per_rep}
- Cost per lead: ${cost_per_lead}
- Pipeline value: ${pipeline_value}

RECOMMENDATIONS
- {list of recommendations}
```

---

*KPI Dashboard*
*Baseline: 500 leads/day, 60% accuracy*
*Target: 25,000 leads/day, >90% accuracy*
*Measurement: Continuous*

---
type: architecture
name: Data Flow Pipeline
layers: 5
---

# Data Flow Pipeline

> "From raw signal to scored lead — the journey of every data point."

## Stage Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ COLLECTION  │────▶│  ANALYSIS   │────▶│   SCORING   │────▶│ PERSISTENCE │────▶│  OUTREACH   │
│  (Collect)  │     │  (Analyze)  │     │   (Score)   │     │  (Persist)  │     │  (Notify)   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                     │                     │                     │                     │
      ▼                     ▼                     ▼                     ▼                     ▼
lead:collected       lead:analyzed        lead:scored        lead:crm_update      lead:outreach
```

## Stage 1: Collection

**Trigger:** Celery Beat every 15 minutes
**Files:** `backend/ingestion/orchestrator.py`, `backend/collectors/*`, `workers/*-actor/`

### Flow
1. `IngestionOrchestrator.run_all()` runs 8 collectors
2. Each collector yields `RawPost` objects
3. `PostDeduplicator` checks Redis content hash cache
4. Valid posts published to Redis Stream `lead:collected`

### Sources
| Source | Collector | Confidence |
|--------|-----------|------------|
| Reddit | `collectors/reddit.py` | 0.40 |
| Hacker News | `collectors/hn.py` | 0.82 |
| Twitter | `collectors/twitter.py` | 0.40 |
| RSS | `collectors/rss.py` | 0.40 |
| GitHub | `collectors/github.py` / `workers/github-actor` | 0.95 |
| ProductHunt | `collectors/producthunt.py` | 0.72 |
| StackOverflow | `collectors/stackoverflow.py` | 0.40 |
| Telegram | `collectors/telegram.py` / `workers/telegram-actor` | 0.40 |
| DPIIT (India) | `workers/dpiit-actor` | 0.78 |
| MCA21 (India) | `workers/mca21-actor` | 0.85 |
| Tracxn | `workers/tracxn-actor` | 0.70 |

---

## Stage 2: Analysis

**Consumer:** `backend/workers/analyzer.py:run_analyzer()`
**Files:** `backend/workers/analyzer.py`, `backend/llm/gemini_service.py`

### Flow
1. Consume from `lead:collected` stream
2. Budget gate: `check_budget(estimated_tokens)`
3. Build source-specific prompt via `_build_prompt()`
4. Call Gemini: `asyncio.to_thread(model.generate_content, ...)`
5. Parse JSON → `AnalyzedLead.model_validate(data)`
6. Compute confidence: `compute_confidence(result, source)`
7. Publish to `lead:analyzed`

### 7-Stage Waterfall (GeminiAnalyzer)
```
1. Budget Gate
2. Prompt Construction (3-layer: persona + source + rules)
3. Async API Call (to_thread wrapper)
4. Parse + Validate (Pydantic v2)
5. Audit Stamp (source, url, model, tokens)
6. Structured Log (structlog)
7. Return AnalyzedLead
```

### Error Handling
- Budget exceeded → regex fallback extraction
- API failure → heuristic classification
- Null result → publish to `lead:failed` stream

---

## Stage 3: Scoring

**Consumer:** `backend/workers/scorer.py:run_scorer()`
**Files:** `backend/workers/scorer.py`, `backend/services/confidence.py`

### Formula
```python
base_raw = (
    0.30 * intent_weight +
    0.25 * icp_fit_norm +
    0.20 * urgency_weight +
    0.15 * confidence +
    0.10 * engagement
)
final_score = base_raw * 100 + temporal_bonus
```

### Temporal Bonus
| Age | Bonus |
|-----|-------|
| Today | +10 |
| This week | +5 |
| This month | 0 |
| Last month | -8 |

### Score Bands
| Band | Range | Action |
|------|-------|--------|
| Hot | >= 80 | Immediate outreach |
| Warm | >= 60 | Queue for outreach |
| Cool | >= 40 | Nurture |
| Cold | < 40 | Drop (not persisted) |

---

## Stage 4: Persistence

**Consumer:** `backend/workers/pipeline.py:persist_scored_leads()`
**Files:** `backend/workers/pipeline.py`, `backend/shared/repository.py`

### Flow
1. Consume from `lead:scored`
2. Filter: only `final_score >= 40`
3. Upsert Post and Lead records
4. Emit domain events:
   - `emit("lead_created")`
   - `emit("lead_enriched")`
   - `emit("lead_scored")`
5. Redis Stream ack

### Deduplication (3-Tier)
```
Tier 1: Exact match (email, linkedin_url, company_domain+title)
Tier 2: Fuzzy match (company name similarity > 0.85)
Tier 3: Vector match (pgvector cosine distance < 0.12)
```

---

## Stage 5: Outreach

**Consumer:** `backend/workers/pipeline.py:run_outreach_consumer()`
**Files:** `backend/workers/pipeline.py`, `backend/bot/notifier.py`

### Flow
1. Consume from `lead:outreach`
2. Generate outreach draft (if missing)
3. Send Telegram notification (if configured)
4. Update CRM (if integrated)

---

## Event Bus Topology

```
┌─────────────────┐
│  lead:collected │───▶ analyzer worker
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  lead:analyzed  │───▶ scorer worker
└─────────────────┘
        │
        ▼
┌─────────────────┐
│   lead:scored   │───▶ persister worker ──▶ PostgreSQL
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  lead:ranked    │───▶ outreach worker
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  lead:outreach  │───▶ telegram notifier
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ lead:crm_update│───▶ DB persistence
└─────────────────┘

┌─────────────────┐
│  system:logs    │───▶ monitoring
└─────────────────┘
```

---

## Celery Beat Schedule

| Task | Interval | Purpose |
|------|----------|---------|
| `collect_and_publish` | 15 min | Run all collectors |
| `refresh_intent_signals` | 30 min | Update intent signals |
| `compute_daily_metrics` | Midnight UTC | Generate daily report |
| `process_dlq_retries` | 5 min | Retry failed leads |
| `monitor_telegram` | 2 hours | Check Telegram channels |

---

## Key Architectural Decisions

1. **Kleppmann Ordering:** DB commit BEFORE Redis publish (analyzer.py)
2. **Fail-Open Budget:** `check_budget()` returns `True` on Redis error
3. **Conservative Bias:** "Better to miss a lead than report a false positive"
4. **Score Threshold:** Only `final_score >= 40` gets persisted
5. **At-Least-Once Delivery:** Redis Streams with consumer groups

---

## Related
- [[GitNexus-Stack]] — Layer 6 (Pipeline & Workers)
- [[LLM-Wiki]] — Layer 5 (LLM Intelligence)
- [[The-Orrery]] — Memory Palace room
- [[Celery-Task-Topology]] — Task chain details

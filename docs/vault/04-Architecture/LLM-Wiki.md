---
version: 2.0
phase: 6
updated: 2026-04-25
---

# LLM Wiki — Lead-iq Intelligence Layer Documentation

> "The brain of the operation. Every lead passes through here."
> 
> **Current Status:** Phase 6 active. Field precision at 12.64%, targeting >75%.

## Wiki Map

- [[LLM-Wiki#Architecture]] — System overview
- [[LLM-Wiki#Gemini-Service]] — Core extraction engine
- [[LLM-Wiki#Cost-Guard]] — Budget enforcement
- [[LLM-Wiki#Source-Prompts]] — Prompt engineering
- [[LLM-Wiki#Schemas]] — Data contracts
- [[LLM-Wiki#Circuit-Breaker]] — Resilience
- [[LLM-Wiki#Embeddings]] — Vector search
- [[LLM-Wiki#ICP-Parsing]] — Natural language ICP
- [[LLM-Wiki#Evaluation]] — Quality measurement
- [[LLM-Wiki#Error-Handling]] — Failure modes
- [[LLM-Wiki#Integration-Points]] — How to extend

---

## Architecture

### File Structure
```
backend/llm/
├── __init__.py          # Exports check_budget, get_budget_status
├── gemini_service.py    # Core extraction, embeddings, vision, ICP
├── cost_guard.py        # Redis-based daily budget (2M tokens)
├── SOURCE_PROMPTS.py    # 8 source-specific prompts + India signals
├── schemas.py           # AnalyzedLead Pydantic v2 model
└── circuit_breaker.py   # Redis-backed circuit breaker
```

### Model Hierarchy
| Purpose | Model | Cost |
|---------|-------|------|
| Bulk extraction | `gemini-2.0-flash-lite` | $0.075/M tokens |
| Scoring/parsing | `gemini-2.0-flash` | $0.10/M tokens |
| Embeddings | `text-embedding-004` | $0.00002/K tokens |
| Vision (team pages) | `gemini-2.0-flash` | $0.10/M tokens |

### Daily Budget
```python
DAILY_TOKEN_BUDGET = 2_000_000  # ~$0.15/day on Flash-Lite
Redis key: gemini:tokens:{YYYY-MM-DD}
TTL: 86,400 seconds (24 hours)
```

---

## Gemini Service

### Entry Points

#### `extract_lead()` — Primary Extraction
```python
async def extract_lead(
    markdown_content: str,
    source: str,           # One of 8 supported sources
    url: str,
) -> dict[str, Any]
```
**Pipeline:**
1. Check budget via `cost_guard.check_budget()`
2. If over budget → `regex_fallback_extract()`
3. Build source-specific prompt via `SOURCE_PROMPTS[source]`
4. Call `asyncio.to_thread(model.generate_content, ...)` — async-safe
5. Parse JSON response
6. Add metadata: `source`, `source_url`, `confidence`
7. Return dict with extracted fields

**Error Handling:**
- Budget exceeded → fallback to regex extraction
- JSON parse error → raise `GeminiExtractionError` (HIGH-035 fixed)
- API error → raise `GeminiExtractionError` with context

#### `get_embedding()` — Semantic Search
```python
async def get_embedding(text: str) -> list[float] | None
```
**Returns:** 768-dimensional vector or `None` if budget exceeded
**Used by:** `icp_service.py` for semantic ICP matching

#### `extract_from_image()` — Vision Extraction
```python
async def extract_from_image(
    image_bytes: bytes,
    instruction: str,
    mime_type: str = "image/png",
) -> dict[str, Any]
```
**Use case:** Team pages, conference slides, screenshots

#### `parse_natural_language_icp()` — ICP Builder
```python
async def parse_natural_language_icp(description: str) -> dict[str, Any]
```
**Input:** "CTOs at Indian SaaS startups 20-200 employees using React"
**Output:** Structured JSON with `target_industries`, `company_sizes`, `required_signals`

#### `compute_confidence()` — Quality Score
```python
def compute_confidence(lead: dict[str, Any], source: str) -> float
```
**Formula:** `field_completeness × source_trust` (see [[LLM-Wiki#Confidence-Formula]])

---

## Cost Guard

### API
```python
async def check_budget(tokens_requested: int) -> bool
    # Returns True → proceed
    # Returns False → use fallback
    # On Redis error → fail-open (returns True)

async def get_budget_status() -> dict
    # {"date", "used", "remaining", "budget", "percent_used"}

async def reset_budget() -> None
    # Admin-only: deletes today's counter
```

### Guarded Call Sites
| File | Function | Budget Check Line |
|------|----------|-------------------|
| `gemini_service.py` | `extract_lead()` | 89 |
| `gemini_service.py` | `get_embedding()` | 204 |
| `gemini_service.py` | `extract_from_image()` | 237 |
| `gemini_service.py` | `parse_natural_language_icp()` | 283 |
| `workers/analyzer.py` | `GeminiAnalyzer.analyze()` | 301 |

---

## Source Prompts

### 3-Layer Architecture

**Layer 1 — Persona + Mission**
```
You are a B2B sales intelligence analyst...
```

**Layer 2 — Source Context**
```
SOURCE: {source}
CONFIDENCE_CEILING: {SOURCE_TRUST[source]}
GOTCHAS: [...]
```

**Layer 3 — Extraction Rules (Colvin/Amodei)**
1. Extract ONLY what is explicitly stated
2. Null for unmentioned fields, never assume
3. Better to miss a lead than report a false positive

### Supported Sources
| Source | Confidence | Quality |
|--------|-----------|---------|
| `github_api` | 0.95 | Verified API |
| `hunter_io` | 0.90 | Email verification |
| `mca21` | 0.85 | Official registry |
| `hacker_news` | 0.82 | Self-posted by founders |
| `dpiit` | 0.78 | Government registry |
| `yourstory` | 0.75 | Editorial |
| `producthunt` | 0.72 | Self-posted |
| `tracxn` | 0.70 | Aggregated |

### India Signals Lookup
```python
INDIA_SIGNALS_LOOKUP: dict[str, dict[str, list[str]]]
# Maps source → domain → signal keywords
# e.g., "yourstory" → "fintech" → ["Razorpay", "PhonePe"]
```

### Phase 6 Improvements
**Status:** IN PROGRESS — See [[Phase-6-Data-Quality-LLM-Prompts]]

Planned enhancements:
- Add 2-3 few-shot examples per source
- Add structured schema injection in prompts
- Add Pydantic `model_validate_json()` enforcement
- Improve regex fallback with source-specific patterns

---

## Schemas

### AnalyzedLead (Pydantic v2)
```python
class AnalyzedLead(BaseModel):
    company_name: str | None
    industry: str | None
    company_size: str | None
    location: str | None
    contact_name: str | None
    contact_title: str | None
    email: str | None
    phone: str | None
    linkedin_url: str | None
    tech_stack: list[str]
    intent_signals: list[str]
    pain_points: list[str]
    funding_stage: str | None
    is_opportunity: bool
    confidence: float
    source: str
    source_url: str
    extracted_at: datetime
```

### Validators (Colvin Rules)
1. `validate_confidence_evidence` — Confidence > 0.7 requires `company_name` or `contact_name`
2. `validate_opportunity_threshold` — `is_opportunity=True` + confidence < 0.35 → auto-reject
3. `validate_intent` / `validate_urgency` — Whitelist enforcement

---

## Circuit Breaker

### States
- `CLOSED` — Normal operation
- `OPEN` — After 5 failures, blocks calls for 60s
- `HALF_OPEN` — Allows test call after recovery timeout

### Redis Key
```
gemini:circuit:{name}  # default name = "gemini"
```

### Usage
```python
from backend.llm.circuit_breaker import get_state, record_failure, record_success

state = get_state("gemini")
if state == "OPEN":
    return fallback_result

try:
    result = await extract_lead(...)
    record_success("gemini")
except Exception:
    record_failure("gemini")
```

---

## Embeddings

### Model
- `text-embedding-004` — 768 dimensions
- Cost: $0.00002 per 1K tokens

### Storage
- PostgreSQL `pgvector` extension
- Columns: `Lead.embedding`, `ICP.embedding`
- Index: HNSW with `vector_cosine_ops`

### Consumers
| File | Function | Usage |
|------|----------|-------|
| `services/icp_service.py` | `find_matching_leads()` | Semantic ICP matching |
| `services/dedup_service.py` | `find_vector_match()` | Tier 3 deduplication |

---

## ICP Parsing

### Natural Language → Structured
```python
# Input
"CTOs at Indian SaaS startups 20-200 employees using React"

# Output
{
  "target_industries": ["saas"],
  "target_company_sizes": ["11-50", "51-200"],
  "required_signals": ["react", "india"],
  "min_confidence": 0.65
}
```

### Consumer
- `backend/services/icp_service.py:parse_icp()` — Converts parsed result to DB model

---

## Evaluation

### Ground Truth
- **File:** `eval/ground_truth.json`
- **Size:** 50 hand-verified records
- **Sources:** 5 (tracxn, hn, github, yourstory, producthunt)

### Methodology
```python
calculate_field_precision(extracted, expected) -> (precision_score, field_matches)
```

### Targets
| Metric | Target | Current |
|--------|--------|---------|
| Overall precision | >75% | 12.64% ⚠️ |
| Per-source | >=70% | — |
| Per-field | >=75% | — |

### CI Integration
```bash
python eval/run_eval.py
# Exit code: 0 = pass, 1 = fail
```

### Phase 6 Focus
**Current precision breakdown:**
- github_profile: 15.71%
- producthunt: 15.71%
- hacker_news: 15.00%
- tracxn: 8.75%
- yourstory: 8.00%

**Worst fields:**
- company_name: 0.00%
- industry: 0.00%
- tech_stack: 0.00%
- email: 0.00%

See [[Phase-6-Data-Quality-LLM-Prompts]] for remediation plan.

---

## Error Handling

### Failure Mode Matrix
| Failure | Handler | Fallback |
|---------|---------|----------|
| Budget exceeded | `cost_guard.py` | Regex extraction |
| JSON parse error | `gemini_service.py` | Raise `GeminiExtractionError` |
| API error | `gemini_service.py` | Raise `GeminiExtractionError` |
| Circuit open | `circuit_breaker.py` | Heuristic classification |
| Redis down | `cost_guard.py` | Fail-open (allow call) |
| Analyzer crash | `analyzer.py` | Heuristic classify |

### DLQ Integration
- Analyzer null results → `lead:failed` stream
- Pipeline task failures → `LeadDLQ` table via Celery signals

---

## Integration Points

### How to Add a New Source
1. Add prompt to `SOURCE_PROMPTS.py`
2. Add confidence ceiling to `services/confidence.py:SOURCE_TRUST`
3. Add India signals to `INDIA_SIGNALS_LOOKUP`
4. Add ground truth cases to `eval/ground_truth.json`
5. Run `python eval/run_eval.py`

### How to Change a Model
1. Update `gemini_service.py:MODELS` dict
2. Update cost estimate in `cost_guard.py` if pricing changes
3. Run eval to verify quality
4. Update this wiki

### How to Add a New LLM Feature
1. Add function to `gemini_service.py`
2. Add budget check as first line
3. Wrap sync calls in `asyncio.to_thread()`
4. Add Pydantic schema to `schemas.py` if output is structured
5. Add tests to `tests/`
6. Update this wiki

---

## Related
- [[GitNexus-Stack]] — Layer 5 context
- [[Data-Flow-Pipeline]] — End-to-end data flow
- [[The-Forge]] — Memory Palace room
- [[CRIT-003]] — Recent fix: broken confidence import
- [[CRIT-004]] — Recent fix: sync blocking calls
- [[HIGH-035]] — Fixed: GeminiExtractionError
- [[Phase-6-Data-Quality-LLM-Prompts]] — Active remediation phase

---

*Wiki updated: 2026-04-25. Next update after Phase 6 eval improvements.*
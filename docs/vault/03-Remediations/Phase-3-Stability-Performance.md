---
phase: 3
name: Stability & Performance
start_date: 2026-04-25
target_date: 2026-04-25
status: resolved
---

# Phase 3: Stability & Performance

## Goal
Fix async anti-patterns, N+1 queries, blocking Redis ops, and analyzer resilience.

## Issues
- [x] [[HIGH-027]] Move pipeline logic from routes to service
- [x] [[HIGH-028]] Move profile scoring from routes to service
- [x] [[HIGH-029]] Fix N+1 queries in LeadRepo
- [x] [[HIGH-030]] Fix N+1 queries in PostRepo
- [x] [[HIGH-033]] Fix DLQ signal handler async anti-pattern
- [x] [[HIGH-034]] Replace Redis KEYS with SCAN
- [x] [[HIGH-035]] Raise GeminiExtractionError instead of error dict
- [x] [[HIGH-036]] Add retry counter to analyzer

---

## Execution Order (GitNexus Bottom-Up)

### Step 1: HIGH-034 — Redis KEYS → SCAN (velocity.py)
**Blast radius:** Only `velocity_tracker.get_top_companies()`
**Rationale:** Infrastructure-layer fix, no dependencies.

| Before | After |
|--------|-------|
| `keys = await self._client.keys(pattern)` | `keys = [k async for k in self._client.scan_iter(match=pattern)]` |

**Verification:** `Redis monitor` shows `SCAN` not `KEYS`.

---

### Step 2: HIGH-033 — DLQ Signal Handler Fix (pipeline.py)
**Blast radius:** Celery task failure signal path
**Rationale:** Pipeline layer, async safety.

**Problem:** `loop.run_until_complete(_capture())` inside Celery signal handler.
**Fix:** Use `asyncio.run_coroutine_threadsafe()` or fire-and-forget `loop.create_task()` with proper error handling.

| Before | After |
|--------|-------|
| `loop.run_until_complete(_capture())` | `asyncio.ensure_future(_capture())` + explicit loop retrieval |

---

### Step 3: HIGH-029 + HIGH-030 — N+1 Query Fixes (repository.py)
**Blast radius:** All consumers of `LeadRepo.list_all()`, `PostRepo.get_by_hash()`
**Rationale:** Data access layer, models must exist.

**LeadRepo.list_all():**
```python
from sqlalchemy.orm import selectinload
q = select(Lead).options(
    selectinload(Lead.post),
).where(Lead.final_score >= min_score)
```

**PostRepo.get_by_hash():**
```python
q = select(Post).options(selectinload(Post.lead)).where(Post.content_hash == content_hash).limit(1)
```

**Verification:** SQLAlchemy echo log shows 1 query for list + posts.

---

### Step 4: HIGH-027 — Move Pipeline Logic from Routes (leads.py)
**Blast radius:** leads.py routes, new `services/pipeline_service.py`
**Rationale:** Business logic in routes violates architecture rules.

**Extract from routes to `PipelineService`:**
- `trigger_miner()` → `PipelineService.trigger_collection()`
- `trigger_ai()` → `PipelineService.trigger_analysis()`

**Route after fix:**
```python
@router.post("/run-miner", response_model=TriggerResponse)
async def trigger_miner(user: CurrentUser) -> TriggerResponse:
    return await pipeline_service.trigger_collection()
```

---

### Step 5: HIGH-028 — Move Profile Scoring from Routes (profile.py)
**Blast radius:** profile.py routes, `services/personalization.py`
**Rationale:** Business logic in routes violates architecture rules.

**Extract from `personalised_leads()` route:**
- Lead fetching with profile context
- Velocity batch fetch
- Per-lead personalized score computation
- Sorting and slicing

→ `services/personalization.py::get_personalized_leads(session, profile_data, limit, min_base_score)`

**Route after fix:**
```python
@router.get("/leads", response_model=list[PersonalizedLeadOut])
async def personalised_leads(
    session: DbSession,
    limit: int = Query(50, ge=1, le=200),
    min_base_score: float = Query(0.0, ge=0.0, le=100.0),
) -> list[PersonalizedLeadOut]:
    return await get_personalized_leads(session, limit, min_base_score)
```

---

### Step 6: HIGH-035 — Raise GeminiExtractionError (gemini_service.py)
**Blast radius:** All callers of `extract_lead()`, `get_embedding()`, `extract_from_image()`, `parse_natural_language_icp()`
**Rationale:** Error dicts silently propagate bad data.

**New exception class:**
```python
class GeminiExtractionError(Exception):
    """Raised when Gemini extraction fails irrecoverably."""
    def __init__(self, message: str, source: str | None = None, url: str | None = None):
        super().__init__(message)
        self.source = source
        self.url = url
```

**Changes per function:**
- `extract_lead()`: Replace `return {"error": ...}` with `raise GeminiExtractionError(...)`
- `get_embedding()`: Replace `return None` on error with `raise GeminiExtractionError(...)`
- `extract_from_image()`: Replace `return {}` on error with `raise GeminiExtractionError(...)`
- `parse_natural_language_icp()`: Replace `return {}` on error with `raise GeminiExtractionError(...)`

**Callers updated:**
- `workers/analyzer.py` — catch `GeminiExtractionError` → send to DLQ
- `services/icp_service.py` — catch and fallback

---

### Step 7: HIGH-036 — Add Retry Counter to Analyzer (analyzer.py)
**Blast radius:** `workers/analyzer.py` consumer loop
**Rationale:** Distinguish transient vs permanent errors.

**Changes:**
1. Add `_retry_counter: dict[str, int]` to track per-message retries
2. `IntegrityError` → permanent (ack + skip)
3. `GeminiExtractionError` → permanent after 3 retries (send to DLQ)
4. `SQLAlchemyError` (connection) → transient, retry 3x then DLQ
5. Other `Exception` → transient, retry 3x then DLQ
6. After max retries: ack the message (don't leave in PEL forever)

---

## Phase 3 Exit Criteria
- [ ] No `loop.run_until_complete()` patterns remain
- [ ] All repository list queries use eager loading
- [ ] No `KEYS` commands in Redis
- [ ] Analyzer handles transient vs permanent errors with retry counter
- [ ] All routes delegate business logic to services
- [ ] Gemini errors raise typed exceptions, not error dicts

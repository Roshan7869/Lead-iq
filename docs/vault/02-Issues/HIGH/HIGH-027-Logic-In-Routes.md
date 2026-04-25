---
severity: high
domain: architecture
status: resolved
phase: 3
file: backend/api/routes/leads.py
line: 103-151
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-027: Pipeline Logic in Routes

## Location
[[The-Forge]] → `backend/api/routes/leads.py:103-151`

## Description
`trigger_miner()` and `trigger_ai()` contained full Celery fallback logic, collector imports, and async task spawning inline. Routes should be thin HTTP adapters.

## Root Cause
Business logic was written directly in route handlers.

## Fix
Extracted all pipeline logic to `backend/services/pipeline_service.py`:
```python
# New service: services/pipeline_service.py
async def trigger_collection() -> TriggerResponse:
    try:
        task = collect_and_publish.delay()
        return TriggerResponse(status="queued", ...)
    except Exception:
        asyncio.create_task(_quick_collect())
        return TriggerResponse(status="running", ...)

# Route after fix:
@router.post("/run-miner")
async def trigger_miner(user: CurrentUser) -> TriggerResponse:
    return await trigger_collection()
```

## Blast Radius
- New file `services/pipeline_service.py`
- Routes now <5 lines each
- Fallback logic is reusable and testable

## Verification
```bash
python -m py_compile backend/services/pipeline_service.py
```

## Related
- [[HIGH-028]] (profile scoring in routes)
- [[The-Forge#Anvil]]

## Commit
- `refactor(routes): extract pipeline logic to pipeline_service.py`

---
severity: critical
domain: pipeline
status: open
phase: 1
file: backend/events/emitter.py
line: 33
created: 2026-04-25
---

# CRIT-009: Events Silently Dropped

## Location
[[The-Orrery]] → `backend/events/emitter.py:33`

## Description
`emit()` is a **synchronous** function that calls `_r.xadd()` (an async coroutine on `aioredis.Redis`) without `await`. The coroutine is never executed; all domain events are silently dropped.

## Root Cause
Missing `await` and `async def` on the `emit` function.

## Current Code
```python
def emit(event_type: str, payload: dict, maxlen: int = 50_000):
    # ...
    _r.xadd(stream, {  # ← async coroutine called without await
        "event_type": event_type,
        "payload": json.dumps(payload),
        "emitted_at": datetime.now(timezone.utc).isoformat(),
    }, maxlen=maxlen)
```

## Fix
```python
async def emit(event_type: str, payload: dict, maxlen: int = 50_000):
    # ...
    await _r.xadd(stream, {
        "event_type": event_type,
        "payload": json.dumps(payload),
        "emitted_at": datetime.now(timezone.utc).isoformat(),
    }, maxlen=maxlen)
```

## Blast Radius
- **6 callers must be updated to `await emit()`:**
  1. `backend/workers/pipeline.py:332-334`
  2. `backend/workers/scorer.py:179`
  3. `backend/services/intent_monitor.py:207`
  4. Any other undiscovered callers

## Verification
```python
import asyncio
from backend.events.emitter import emit

async def test():
    await emit("test_event", {"foo": "bar"})
    # Check Redis stream has entry

asyncio.run(test())
```

## Related
- [[CRIT-010]] Celery async anti-pattern
- [[The-Orrery#Broken-Links]]

## Commit
`fix(events): make emit async with await on redis xadd`

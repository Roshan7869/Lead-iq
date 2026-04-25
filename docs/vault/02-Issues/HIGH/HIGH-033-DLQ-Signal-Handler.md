---
severity: high
domain: pipeline
status: resolved
phase: 3
file: backend/workers/pipeline.py
line: 60-64
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-033: DLQ Signal Handler Async Anti-Pattern

## Location
[[The-Orrery]] → `backend/workers/pipeline.py:60-64`

## Description
The Celery `task_failure` signal handler used `loop.run_until_complete()` inside a potentially non-event-loop thread, causing `RuntimeError` in some execution contexts.

## Root Cause
`asyncio.get_event_loop()` returns the running loop or creates a new one. Calling `run_until_complete()` on a running loop crashes.

## Fix
```python
# Before:
loop = asyncio.get_event_loop()
if loop.is_running():
    loop.create_task(_capture())
else:
    loop.run_until_complete(_capture())

# After:
try:
    loop = asyncio.get_running_loop()
    loop.create_task(_capture())
except RuntimeError:
    # No running loop in this thread → fire-and-forget with new loop
    asyncio.run(_capture())
```

## Blast Radius
- All Celery task failures now safely route to DLQ
- No more `RuntimeError` in signal handlers

## Verification
```python
# Simulate a failing task:
@celery_app.task
def test_fail():
    raise ValueError("test")

# Run task → check DLQ has entry, no RuntimeError
```

## Related
- [[CRIT-010]] (Celery async anti-pattern in actors)
- [[HIGH-036]] (analyzer retry counter)
- [[The-Orrery#Gears]]

## Commit
- `fix(pipeline): safe async handling in DLQ signal handler`

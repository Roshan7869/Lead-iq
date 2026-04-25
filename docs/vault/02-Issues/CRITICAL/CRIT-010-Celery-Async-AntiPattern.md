---
severity: critical
domain: pipeline
status: open
phase: 1
file: backend/workers/actors.py
line: 91-97,130-136
created: 2026-04-25
---

# CRIT-010: Celery Async Anti-Pattern

## Location
[[The-Orrery]] → `backend/workers/actors.py`

## Description
Celery tasks call `loop.run_until_complete()` inside sync task bodies. Will crash with `RuntimeError: This event loop is already running` inside Celery worker threads.

## Root Cause
Incorrect async/await pattern inside sync Celery task functions.

## Current Code
```python
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        return loop.run_until_complete(_run())
    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_run())
except Exception as exc:
    ...
```

## Fix
Option A — Use `asyncio.run()`:
```python
try:
    return asyncio.run(_run())
except Exception as exc:
    ...
```

Option B — Use Celery 5.4+ native async tasks:
```python
@celery_app.task
async def collect_github_task(...):
    # async def task body
    await _run()
```

## Blast Radius
- `backend/workers/actors.py` — 3 tasks affected
- `backend/workers/pipeline.py` — `_run_async()` helper has same issue
- All Celery workers will crash on task execution

## Verification
```bash
# Trigger a Celery actor task
celery -A backend.workers.pipeline call backend.workers.actors.collect_github_task → succeeds
```

## Related
- [[CRIT-009]] Events silently dropped
- [[The-Orrery#Gears]]

## Commit
`fix(workers): replace loop.run_until_complete with asyncio.run`

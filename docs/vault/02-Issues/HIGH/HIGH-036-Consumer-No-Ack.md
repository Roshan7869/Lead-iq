---
severity: high
domain: pipeline
status: resolved
phase: 3
file: backend/workers/analyzer.py
line: 578-580
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-036: Analyzer Consumer No Retry Counter

## Location
[[The-Orrery]] → `backend/workers/analyzer.py:578-580`

## Description
The analyzer consumer had a bare `except Exception` that logged the error but did NOT ack the message. Failed messages accumulated in the Pending Entries List (PEL) forever, consuming memory and never being retried.

## Root Cause
No retry mechanism — messages were left in limbo.

## Fix
Added per-event retry counter with transient vs permanent classification:

```python
_MAX_RETRIES = 3
_retry_counter: dict[str, int] = {}

# Permanent errors (ack immediately, send to DLQ):
- IntegrityError → duplicate lead
- GeminiExtractionError → bad API response
- ValueError/TypeError → bad data

# Transient errors (retry up to 3x):
- SQLAlchemyError → DB connection issues
- Other Exception → unknown

# After max retries → ack + send to lead:failed stream
```

## Blast Radius
- All stream consumers now have explicit retry logic
- Memory leak from unacked messages is fixed
- Failed messages are visible in `lead:failed` stream

## Verification
```python
# Inject a failing event:
await redis_stream.publish("lead:collected", {
    "body": "test", "source": "test", "url": "http://test"
})

# Check after 3 retries:
# - Event acked from lead:collected
# - Entry in lead:failed stream
```

## Related
- [[HIGH-033]] (DLQ signal handler)
- [[HIGH-035]] (GeminiExtractionError)
- [[The-Orrery#Gears]]

## Commit
- `feat(analyzer): add retry counter with transient vs permanent error handling`

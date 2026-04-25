---
severity: high
domain: security
status: resolved
phase: 2
file: backend/api/routes/leads.py
line: 53-68
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-017: Silent Exception Swallowing in Leads Route

## Location
[[The-Gatehouse]] → `backend/api/routes/leads.py:53-68`

## Description
`list_leads()` caught `SQLAlchemyError` and bare `Exception` and returned an empty list without logging. Database outages, schema mismatches, and bugs were completely invisible.

## Root Cause
Exception handlers returned a silent fallback without any observability.

## Fix
```python
import logging
logger = logging.getLogger(__name__)

except SQLAlchemyError as exc:
    logger.warning("Database error in list_leads: %s", exc)
    return LeadListResponse(leads=[], total=0, page=1, page_size=limit)
except Exception as exc:
    logger.error("Unexpected error in list_leads: %s", exc)
    return LeadListResponse(leads=[], total=0, page=1, page_size=limit)
```

## Blast Radius
- Sentry/log aggregation now receives these events
- Alerts can be built on `logger.error` frequency

## Verification
1. Temporarily break `DATABASE_URL` to point to a non-existent host
2. Call `GET /api/leads` with valid auth
3. Check logs → should show `Database error in list_leads`

## Related
- [[HIGH-037]] (auth hook error swallowing)
- [[The-Gatehouse#Moat]]

## Commit
- `fix(leads): log errors instead of silent swallowing`

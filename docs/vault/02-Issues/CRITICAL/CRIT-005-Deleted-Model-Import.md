---
severity: critical
domain: data-layer
status: open
phase: 1
file: backend/services/dedup_service.py
line: 25
created: 2026-04-25
---

# CRIT-005: Deleted Model Import

## Location
[[The-Archive]] → `backend/services/dedup_service.py:25`

## Description
`from backend.models.lead import Lead` imports a module that was **deleted** (`backend/models/lead.py` no longer exists). This causes an `ImportError` on application startup, preventing the dedup service (and by extension, the pipeline) from loading.

## Root Cause
`lead.py` was moved/refactored to `backend/shared/models.py` but the import was not updated.

## Current Code
```python
from backend.models.lead import Lead  # ← DELETED MODULE
```

## Fix
```python
from backend.shared.models import Lead  # ← CORRECT LOCATION
```

## Blast Radius
- `backend/services/dedup_service.py` — all functions use `Lead`
- `backend/workers/pipeline.py:471` — imports `find_duplicate, merge_leads` from dedup_service
- If dedup_service fails to import, Celery `dedup_lead` task crashes on startup

## Verification
```bash
python -c "from backend.services.dedup_service import find_duplicate" → No ImportError
```

## Related
- [[CRIT-006]] Missing embedding column (same model)
- [[The-Archive#Missing-Pages]]

## Commit
`fix(dedup): update Lead import from deleted models.lead to shared.models`

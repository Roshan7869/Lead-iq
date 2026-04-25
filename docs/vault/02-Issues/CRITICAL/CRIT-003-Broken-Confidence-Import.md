---
severity: critical
domain: architecture
status: open
phase: 1
file: backend/llm/gemini_service.py
line: 341
created: 2026-04-25
---

# CRIT-003: Broken confidence.py Import

## Location
[[The-Forge]] → `backend/llm/gemini_service.py:341`

## Description
Imports `backend.llm.confidence` which **does not exist**. Raises `ModuleNotFoundError` on every successful extraction when confidence is computed.

## Root Cause
The confidence module was moved to `backend/services/confidence.py` but the import path was not updated.

## Current Code
```python
from backend.llm.confidence import SOURCE_TRUST, FIELD_WEIGHTS, compute_field_score
```

## Fix
```python
from backend.services.confidence import SOURCE_TRUST, FIELD_WEIGHTS, compute_field_score
```

## Blast Radius
- `backend/llm/gemini_service.py:125` — `compute_confidence()` call inside `extract_lead()`
- Any successful extraction → confidence computation → crash

## Verification
```bash
python -c "from backend.llm.gemini_service import extract_lead" → No ImportError
```

## Related
- [[The-Forge#Anvil]]

## Commit
`fix(llm): correct confidence import path from services module`

---
severity: critical
domain: data-layer
status: open
phase: 1
file: backend/shared/models.py
line: 63-117
created: 2026-04-25
---

# CRIT-006: Lead Model Missing Embedding Column

## Location
[[The-Archive]] → `backend/shared/models.py` (Lead class)

## Description
The Alembic migration adds `embedding vector(768)` to the `leads` table, but the `Lead` SQLAlchemy model does not declare this column. `dedup_service.py` references `Lead.embedding` which will raise `AttributeError`.

## Root Cause
ORM model not updated after migration was written.

## Current Code (missing in Lead class)
```python
# NOT PRESENT — needs to be added
# embedding = Column(Vector(768), nullable=True)
```

## Fix
```python
from pgvector.sqlalchemy import Vector

class Lead(Base):
    __tablename__ = "leads"
    # ... existing columns ...
    embedding = Column(Vector(768), nullable=True)  # ← ADD THIS
```

## Blast Radius
- `backend/services/dedup_service.py:190` — `Lead.embedding.cosine_distance(embedding)`
- Any query accessing `lead.embedding`

## Verification
```bash
python -c "from backend.shared.models import Lead; print(Lead.embedding)" → Column object
```

## Related
- [[CRIT-005]] Deleted model import
- [[The-Archive#Missing-Pages]]

## Commit
`fix(models): add embedding column to Lead ORM model`

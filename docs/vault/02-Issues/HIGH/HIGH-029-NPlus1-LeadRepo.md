---
severity: high
domain: data-layer
status: resolved
phase: 3
file: backend/shared/repository.py
line: 84-96
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-029: N+1 Queries in LeadRepo.list_all()

## Location
[[The-Archive]] → `backend/shared/repository.py:84-96`

## Description
`LeadRepo.list_all()` returned leads without eager-loading the `post` relationship. Every access to `lead.post` triggered an additional SQL query.

## Root Cause
Missing `selectinload(Lead.post)` in the query.

## Fix
```python
from sqlalchemy.orm import selectinload

q = (
    select(Lead)
    .options(selectinload(Lead.post))
    .where(Lead.final_score >= min_score)
)
```

## Blast Radius
- All callers of `list_all()` benefit
- SQLAlchemy echo log now shows 1 query instead of N+1

## Verification
```python
# With SQLALCHEMY_ECHO=1:
# Before: 1 query for leads + 1 query per lead.post access
# After:  1 query with JOIN for posts
```

## Related
- [[HIGH-030]] (N+1 in PostRepo)
- [[The-Archive#Scrolls]]

## Commit
- `fix(repository): add selectinload to LeadRepo.list_all`

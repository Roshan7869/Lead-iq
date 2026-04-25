---
severity: high
domain: data-layer
status: resolved
phase: 3
file: backend/shared/repository.py
line: 35-40
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-030: N+1 Queries in PostRepo.get_by_hash()

## Location
[[The-Archive]] → `backend/shared/repository.py:35-40`

## Description
`PostRepo.get_by_hash()` returned a post without eager-loading the `lead` relationship. Every access to `post.lead` triggered an additional SQL query.

## Root Cause
Missing `selectinload(Post.lead)` in the query.

## Fix
```python
q = (
    select(Post)
    .options(selectinload(Post.lead))
    .where(Post.content_hash == content_hash)
    .limit(1)
)
```

## Blast Radius
- `analyzer.py` dedup path no longer triggers extra queries
- SQLAlchemy echo log shows 1 query instead of 2

## Verification
```python
# With SQLALCHEMY_ECHO=1:
# Before: SELECT posts + SELECT leads WHERE post_id = ?
# After:  SELECT posts JOIN leads ON posts.id = leads.post_id
```

## Related
- [[HIGH-029]] (N+1 in LeadRepo)
- [[The-Archive#Scrolls]]

## Commit
- `fix(repository): add selectinload to PostRepo.get_by_hash`

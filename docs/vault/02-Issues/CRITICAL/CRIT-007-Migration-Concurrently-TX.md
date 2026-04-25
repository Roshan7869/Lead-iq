---
severity: critical
domain: data-layer
status: open
phase: 1
file: backend/alembic/versions/20260404_120000_add_hnsw_indexes_and_constraints.py
line: 38-62
created: 2026-04-25
---

# CRIT-007: CREATE INDEX CONCURRENTLY Inside Transaction

## Location
[[The-Archive]] → `backend/alembic/versions/20260404_120000_add_hnsw_indexes_and_constraints.py`

## Description
PostgreSQL forbids `CREATE INDEX CONCURRENTLY` inside a transaction block. Alembic runs migrations inside a transaction by default. This migration will fail at runtime.

## Root Cause
Using `CREATE INDEX CONCURRENTLY` without committing the transaction first.

## Current Code
```python
op.execute("CREATE INDEX CONCURRENTLY idx_leads_embedding ON leads USING hnsw (embedding vector_cosine_ops)")
```

## Fix
```python
# Commit current transaction before CONCURRENTLY
op.execute("COMMIT")
op.execute("CREATE INDEX CONCURRENTLY idx_leads_embedding ON leads USING hnsw (embedding vector_cosine_ops)")
```

## Blast Radius
- DB deployment scripts
- Fresh database setup
- `alembic upgrade head`

## Verification
```bash
alembic upgrade head → succeeds without error
```

## Related
- [[CRIT-008]] ICP score mismatch (same migration file)
- [[The-Archive#Index-Cards]]

## Commit
`fix(migrations): commit tx before CREATE INDEX CONCURRENTLY`

---
severity: critical
domain: data-layer
status: open
phase: 1
file: backend/alembic/versions/20260404_120000_add_hnsw_indexes_and_constraints.py
line: 51-53,84-89
created: 2026-04-25
---

# CRIT-008: ICP Score Column Name Mismatch

## Location
[[The-Archive]] → Same migration as [[CRIT-007]]

## Description
The migration creates composite index and CHECK constraint on `icp_score`, but the `Lead` model defines `icp_fit_score` (Float, 0-100). The column name mismatch means the migration references a non-existent column.

## Root Cause
Migration written before ORM model naming was finalized.

## Current Migration Code
```sql
CREATE INDEX CONCURRENTLY idx_lead_icp ON leads (icp_score, created_at);
ALTER TABLE leads ADD CONSTRAINT ck_lead_icp_range CHECK (icp_score BETWEEN 0 AND 1);
```

## Fix
```sql
CREATE INDEX CONCURRENTLY idx_lead_icp ON leads (icp_fit_score, created_at);
ALTER TABLE leads ADD CONSTRAINT ck_lead_icp_range CHECK (icp_fit_score BETWEEN 0.0 AND 100.0);
```

## Blast Radius
- Same migration file as [[CRIT-007]]
- `backend/shared/models.py` (Lead.icp_fit_score)

## Verification
```bash
alembic upgrade head → DB schema matches ORM
```

## Related
- [[CRIT-007]] Migration transaction issue (same file)
- [[The-Archive#Damaged-Bindings]]

## Commit
`fix(migrations): align icp_score column name with ORM icp_fit_score`

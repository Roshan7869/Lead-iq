---
type: domain
name: Data Layer
door: The-Archive
issues: 20
severity: critical
---

# The Archive — Data Layer Domain

> "Where all knowledge is stored. Some scrolls are missing. Some bindings are damaged."

## Scrolls (SQLAlchemy Models)
- `backend/shared/models.py` — [[CRIT-006]] 🔴 Missing embedding column, [[HIGH-021]] Incomplete schema, [[HIGH-022]] Missing events relationship, [[HIGH-024]] Integer PKs
- `backend/models/lead_dlq.py` — [[HIGH-023]] Missing FK on original_lead_id
- `backend/models/lead_event.py` — Medium — Missing updated_at
- `backend/models/icp.py` — Medium — Runtime try/except for pgvector

## Index Cards (Alembic Migrations)
- `backend/alembic/versions/20260404_120000_*.py` — [[CRIT-007]] 🔴 CREATE INDEX CONCURRENTLY inside tx, [[CRIT-008]] 🔴 icp_score vs icp_fit_score mismatch
- `backend/alembic/versions/20260406_0003_*.py` — [[HIGH-026]] Destructive downgrade

## Missing Pages
- `backend/models/lead.py` — **DELETED** (was replaced by `backend/shared/models.py`)
- `backend/services/dedup_service.py:25` — [[CRIT-005]] 🔴 Still imports deleted file

## Damaged Bindings
- `Feedback` — Integer PK, missing updated_at
- `QuotaUsage` — Integer PK, missing created_at
- `UserProfile` — Integer PK
- `Lead` — Missing email, linkedin_url, company_domain, title, location, funding_stage, tech_stack, website, founded_year, intent_signals, source, source_url
- Inconsistent UUID formats: `as_uuid=False` vs `as_uuid=True`

## N+1 Queries
- `backend/shared/repository.py:84-96` — [[HIGH-029]] LeadRepo.list_all() no eager loading
- `backend/shared/repository.py:35-40` — [[HIGH-030]] PostRepo.get_by_hash() no eager loading

## Fix Order
1. [[CRIT-005]] Fix deleted model import
2. [[CRIT-006]] Add embedding column to Lead
3. [[CRIT-007]] Fix migration CONCURRENTLY in transaction
4. [[CRIT-008]] Fix icp_score vs icp_fit_score mismatch
5. [[HIGH-021]] Add missing columns to Lead model
6. [[HIGH-022]] Add events relationship to Lead
7. [[HIGH-023]] Add FK constraint to LeadDLQ
8. [[HIGH-024]] Migrate Integer PKs to UUID
9. [[HIGH-025]] Use DbSession dependency in leads routes
10. [[HIGH-026]] Add IF EXISTS to downgrade
11. [[HIGH-029]] Add selectinload to LeadRepo
12. [[HIGH-030]] Add selectinload to PostRepo

## Related
- [[The-Citadel]] ← Back to hub
- [[Phase-1-Stop-the-Bleeding]] ← Active phase
- [[Database-Schema]] ← Reference doc

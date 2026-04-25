---
phase: 7
name: Remaining Issues (MEDIUM + LOW)
type: remediation
dependencies: [[Phase-6-Data-Quality-LLM-Prompts]]
start_date: 2026-04-26
target_date: 2026-04-27
status: pending
---

# Phase 7: Remaining Issues — 55 Issues (33 MEDIUM + 16 LOW + 6 HIGH)

## Goal
Clear all remaining issues to reach 0 open items.

## Remaining Count
| Severity | Count | Status |
|----------|-------|--------|
| HIGH | 6 | 🔴 Active |
| MEDIUM | 33 | 🟡 Pending |
| LOW | 16 | 🟢 Pending |
| **TOTAL** | **55** | **In Progress** |

## The 6 Remaining HIGH Issues

### HIGH-021: Lead Schema Incomplete
**Domain:** Data Layer  
**File:** `backend/shared/models.py`  
**Issue:** Missing columns in Lead model (e.g., `linkedin_url`, `twitter_handle`, `angel_url`)  
**Fix:** Audit full schema vs frontend expectations, add missing columns with migration  
**Verification:** `alembic revision --autogenerate -m "add missing lead columns"`

### HIGH-022: Missing Events Relationship
**Domain:** Data Layer  
**File:** `backend/shared/models.py`  
**Issue:** Lead model lacks relationship to LeadEvent table  
**Fix:** Add `events: Mapped[list[LeadEvent]] = relationship(...)`  
**Verification:** `Lead.events` accessible via SQLAlchemy

### HIGH-023: DLQ Missing FK
**Domain:** Data Layer  
**File:** `backend/models/lead_dlq.py`  
**Issue:** LeadDLQ table has no foreign key to Lead  
**Fix:** Add `lead_id: Mapped[UUID] = mapped_column(ForeignKey("leads.id"))`  
**Verification:** DLQ entries link back to original leads

### HIGH-024: Integer PKs
**Domain:** Data Layer  
**Files:** `backend/shared/models.py`, `backend/models/lead_event.py`  
**Issue:** Some tables still use Integer PKs instead of UUID  
**Fix:** Migrate to UUID (or document intentional exception)  
**Blast Radius:** Any code doing `lead.id == 1` comparisons

### HIGH-025: Manual Session Bypass
**Domain:** Data Layer  
**File:** `backend/shared/db.py`  
**Issue:** Some code manually creates sessions instead of using dependency injection  
**Fix:** Replace manual `sessionmaker()` calls with `get_db()` dependency  
**Verification:** `grep -rn "sessionmaker\|create_engine" backend/api/routes/`

### HIGH-026: Destructive Downgrade
**Domain:** Data Layer  
**File:** `backend/alembic/versions/*.py`  
**Issue:** Some downgrade migrations drop columns with data loss  
**Fix:** Add data backup steps before destructive downgrades  
**Verification:** Review all `op.drop_column()` in downgrade functions

## MEDIUM Issues Overview (33)

| ID | Domain | Summary | Effort |
|----|--------|---------|--------|
| MED-001 | Security | CORS too permissive in dev mode | 15m |
| MED-002 | Security | Rate limiting missing on public endpoints | 30m |
| MED-003 | Security | Log sanitization incomplete | 20m |
| MED-004 | Architecture | Missing healthcheck endpoint | 15m |
| MED-005 | Architecture | Docker compose missing depends_on | 10m |
| MED-006 | Architecture | No graceful shutdown for Celery | 30m |
| MED-007 | Data | Missing indexes on frequent queries | 20m |
| MED-008 | Data | No soft delete for leads | 1h |
| MED-009 | Data | Updated_at not auto-updated | 15m |
| MED-010 | Frontend | Loading states inconsistent | 30m |
| MED-011 | Frontend | Error boundaries missing | 1h |
| MED-012 | Frontend | Accessibility: missing aria labels | 45m |
| ... | ... | ... | ... |

See full list in `docs/vault/02-Issues/MEDIUM/`

## LOW Issues Overview (16)

| ID | Domain | Summary | Effort |
|----|--------|---------|--------|
| LOW-001 | Code | Trailing whitespace in 12 files | 10m |
| LOW-002 | Code | Unused imports in 8 files | 15m |
| LOW-003 | Docs | README outdated (still shows v1 features) | 30m |
| LOW-004 | Config | .env.example missing 3 new variables | 10m |
| ... | ... | ... | ... |

See full list in `docs/vault/02-Issues/LOW/`

## GitNexus Stack Execution Order

```
Layer 3: Data Access (HIGH-021 → HIGH-026)
  → Layer 4: Business Logic (MEDIUM data issues)
    → Layer 2: API Gateway (MEDIUM auth issues)
      → Layer 6: Pipeline (MEDIUM worker issues)
        → Layer 1: Config (LOW config issues)
          → Layer 7: Telemetry (LOW eval issues)
```

## Automation Strategy

### Bulk Fixes (Scriptable)
```bash
# Trailing whitespace
find backend/ -name "*.py" -exec sed -i 's/[[:space:]]*$//' {} +

# Unused imports
ruff check --select F401 --fix backend/

# Sort imports
isort backend/
```

### Manual Fixes (Requires Review)
- HIGH-021 through HIGH-026 (schema changes)
- MED-008 (soft delete — business logic)
- MED-011 (error boundaries — React)

## Phase 7 Exit Criteria
- [ ] 0 HIGH issues remaining
- [ ] <10 MEDIUM issues remaining
- [ ] <5 LOW issues remaining
- [ ] All schema changes have migrations
- [ ] `pytest backend/tests/ -q` still passes
- [ ] `npm run build` still passes
- [ ] Security scan still clean

## Daily Note Template
```markdown
---
date: YYYY-MM-DD
phase: 7
---

# Day N — Remaining Issues

## Fixes Applied
| Issue | File | Change | Status |
|-------|------|--------|--------|
| MED-XXX | `path/to/file.py` | Description | ✅ Fixed |

## Running Count
- HIGH: X/6
- MEDIUM: X/33
- LOW: X/16

## Blockers
- None / [describe]
```

## Related
- [[The-Citadel]] — Current status tracker
- [[GitNexus-Stack]] — Layer-by-layer remediation order
- [[Phase-6-Data-Quality-LLM-Prompts]] — Previous phase
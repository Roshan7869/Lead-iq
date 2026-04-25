---
phase: 1
name: Stop the Bleeding
start_date: 2026-04-25
target_date: 2026-04-26
status: in-progress
---

# Phase 1: Stop the Bleeding

## Goal
Fix all 14 CRITICAL issues. The app must start and basic security must work.

## Issues
| # | Issue | File | Action | Status |
|---|-------|------|--------|--------|
| 1 | [[CRIT-001]] | `backend/api/routes/leads.py:32,73` | Add `user: CurrentUser` | ✅ |
| 2 | [[CRIT-002]] | `backend/api/routes/admin.py:178-188` | Rename `result` → `table_result` | ✅ |
| 3 | [[CRIT-003]] | `backend/llm/gemini_service.py:341` | Fix import path | ✅ |
| 4 | [[CRIT-004]] | `backend/llm/gemini_service.py:110,208,242,308` | Wrap sync calls in `asyncio.to_thread()` | ✅ |
| 5 | [[CRIT-005]] | `backend/services/dedup_service.py:25` | Fix import from deleted model | ✅ |
| 6 | [[CRIT-006]] | `backend/shared/models.py:63-117` | Add `embedding` column | ✅ |
| 7 | [[CRIT-007]] | `backend/alembic/versions/20260404_120000_*.py` | Fix CONCURRENTLY in transaction | ✅ |
| 8 | [[CRIT-008]] | Same migration + `shared/models.py` | Fix `icp_score` vs `icp_fit_score` | ✅ |
| 9 | [[CRIT-009]] | `backend/events/emitter.py:33` | Make `emit` async | ✅ |
| 10 | [[CRIT-010]] | `backend/workers/actors.py:91-97,130-136` | Fix Celery async anti-pattern | ✅ |
| 11 | [[CRIT-011]] | `src/hooks/use-auth.tsx`, `use-leads.tsx`, `use-profile.tsx` | Fix memory leaks | ✅ |
| 12 | [[CRIT-012]] | `src/hooks/use-leads.tsx:32` | Add auth header | ✅ |
| 13 | [[CRIT-013]] | `tsconfig.json` | Enable strict mode | ✅ |
| 14 | [[CRIT-014]] | `backend/api/routes/admin.py:183` | Fix SQL injection f-string | ✅ |

## Quick Wins (Session 1)
All 14 CRITICAL issues have been fixed in this session:
1. **CRIT-001** — Added `user: CurrentUser` to lead endpoints
2. **CRIT-002** — Renamed `result` → `table_result` in deploy_check loop
3. **CRIT-003** — Fixed broken confidence import path
4. **CRIT-004** — Wrapped sync Gemini calls in `asyncio.to_thread()`
5. **CRIT-005** — Fixed deleted model import
6. **CRIT-006** — Added `embedding` column to Lead model
7. **CRIT-007** — Fixed `CREATE INDEX CONCURRENTLY` in transaction
8. **CRIT-008** — Fixed `icp_score` vs `icp_fit_score` mismatch
9. **CRIT-009** — Made `emit()` async with `await`
10. **CRIT-010** — Fixed Celery async anti-pattern
11. **CRIT-011** — Fixed frontend memory leaks in all hooks
12. **CRIT-012** — Added `Authorization` header to lead fetches
13. **CRIT-013** — Enabled TypeScript strict mode
14. **CRIT-014** — Replaced f-string SQL with bound parameters

## Progress Log
| Date | Issue | Status | Commit |
|------|-------|--------|--------|
| 2026-04-25 | CRIT-001 | resolved | — |
| 2026-04-25 | CRIT-002 | resolved | — |
| 2026-04-25 | CRIT-003 | resolved | — |
| 2026-04-25 | CRIT-004 | resolved | — |
| 2026-04-25 | CRIT-005 | resolved | — |
| 2026-04-25 | CRIT-006 | resolved | — |
| 2026-04-25 | CRIT-007 | resolved | — |
| 2026-04-25 | CRIT-008 | resolved | — |
| 2026-04-25 | CRIT-009 | resolved | — |
| 2026-04-25 | CRIT-010 | resolved | — |
| 2026-04-25 | CRIT-011 | resolved | — |
| 2026-04-25 | CRIT-012 | resolved | — |
| 2026-04-25 | CRIT-013 | resolved | — |
| 2026-04-25 | CRIT-014 | resolved | — |

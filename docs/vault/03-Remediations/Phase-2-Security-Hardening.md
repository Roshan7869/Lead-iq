---
phase: 2
name: Security Hardening
start_date: 2026-04-25
target_date: 2026-04-25
status: resolved
---

# Phase 2: Security Hardening

## Goal
Remove hardcoded defaults, fix auth leaks, add token revocation.

## Issues
- [x] [[HIGH-015]] Hardcoded DB Password
- [x] [[HIGH-016]] Hardcoded Admin Username
- [x] [[HIGH-017]] Silent Exception Swallowing
- [x] [[HIGH-018]] JWT Query Param Leak
- [x] [[HIGH-019]] MCP Unauthenticated
- [x] [[HIGH-020]] Stats Unauthenticated
- [x] [[HIGH-047]] JWT Secret Caching
- [x] [[HIGH-048]] Refresh Token Blocklist

## Progress Log
| Date | Issue | Status | Commit |
|------|-------|--------|--------|
| 2026-04-25 | HIGH-015 | resolved | Removed DATABASE_URL default |
| 2026-04-25 | HIGH-016 | resolved | Removed ADMIN_USERNAME default |
| 2026-04-25 | HIGH-017 | resolved | Added structlog to leads route |
| 2026-04-25 | HIGH-018 | resolved | Replaced query param with OptionalUser dep |
| 2026-04-25 | HIGH-019 | resolved | Removed empty-key MCP bypass |
| 2026-04-25 | HIGH-020 | resolved | Added CurrentUser to stats endpoint |
| 2026-04-25 | HIGH-047 | resolved | Read settings dynamically in auth functions |
| 2026-04-25 | HIGH-048 | resolved | Added in-memory token blocklist + revocation |

## Phase 2 Exit Criteria
- [x] No hardcoded secrets in config
- [x] All endpoints (except login/register) require auth
- [x] JWT refresh tokens can be revoked
- [x] Security scan passes (no f-string SQL, no hardcoded creds)

## Next Phase
[[Phase-3-Stability-Performance]]

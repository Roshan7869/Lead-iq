---
severity: high
domain: frontend
status: resolved
phase: 1/4
file: src/hooks/use-leads.tsx
line: 32
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-042: API Auth Header Missing

## Location
[[The-Gallery]] → `src/hooks/use-leads.tsx`

## Description
The lead fetch request didn't include the `Authorization` header, so authenticated users saw demo data instead of real leads.

## Root Cause
Missing `getAuthHeader()` in the `fetch` call.

## Fix
Added in Phase 1. Verified still present after Phase 4 React Query migration:
```typescript
const res = await fetch('/api/leads', {
  headers: getAuthHeader(),
});
```

## Verification
```bash
curl -H "Authorization: Bearer $TOKEN" /api/leads → 200 with real data
curl /api/leads → 401 (no demo fallback in production)
```

## Related
- [[CRIT-012]] (missing auth headers)
- [[HIGH-043]] (demoLeads fallback)
- [[The-Gallery#Easels]]

## Commit
- `fix(frontend): add auth header to lead fetch`

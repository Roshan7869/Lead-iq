---
severity: critical
domain: frontend
status: open
phase: 1
file: src/hooks/use-leads.tsx
line: 32
created: 2026-04-25
---

# CRIT-012: Missing Auth Headers in API Calls

## Location
[[The-Gallery]] → `src/hooks/use-leads.tsx:32`

## Description
The frontend does NOT send the `Authorization` header when fetching leads. The Next.js API route (`src/app/api/leads/route.ts`) forwards `req.headers.get("authorization")` to the backend, but the frontend fetch omits it. Authenticated users never see their real leads — they always see `demoLeads`.

## Root Cause
Missing `Authorization` header in the `fetch()` call.

## Current Code
```typescript
const res = await fetch('/api/leads');  // ← NO AUTH HEADER
```

## Fix
```typescript
import { getAuthHeader } from '@/lib/auth-client';

const res = await fetch('/api/leads', {
  headers: getAuthHeader(),  // ← ADD THIS
});
```

## Blast Radius
- `src/hooks/use-leads.tsx` — all lead fetches
- `src/app/api/leads/route.ts` — already forwards headers correctly
- User experience: finally sees real data instead of demo

## Verification
- Log in → Overview shows real leads from backend, not demo data

## Related
- [[CRIT-001]] Unauthenticated leads (backend fix)
- [[HIGH-042]] API auth header missing
- [[The-Gallery#Cracked-Frames]]

## Commit
`fix(frontend): add Authorization header to lead fetches`

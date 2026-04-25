---
phase: 4
name: Frontend Quality
start_date: 2026-04-25
target_date: 2026-04-25
status: resolved
---

# Phase 4: Frontend Quality

## Goal
Fix memory leaks, migrate to React Query, fix accessibility, error handling, and type safety.

## Issues
- [x] [[HIGH-037]] Auth hook error swallowing
- [x] [[HIGH-038]] Profile save errors not surfaced
- [x] [[HIGH-039]] Migrate hooks to React Query
- [x] [[HIGH-040]] Priority icon strings instead of components
- [x] [[HIGH-041]] Unsafe `as any` cast in enhanced-lead-card
- [x] [[HIGH-042]] API auth headers verification
- [x] [[HIGH-043]] PATCH route only updates demoLeads
- [x] [[HIGH-044]] Division by zero in command center

---

## Execution Order

### Step 1: HIGH-037 + HIGH-038 — Error Handling in Hooks
**Files:** `src/hooks/use-auth.tsx`, `src/hooks/use-profile.tsx`

**use-auth.tsx:**
- Wrap `init()` in try/catch/finally
- Ensure `setIsLoading(false)` always fires
- Log error via `console.error` (development only)

**use-profile.tsx:**
- `saveProfile` catches `syncToBackend` errors
- Surface error to caller via return value or toast

### Step 2: HIGH-039 — React Query Migration (Pragmatic)
**Files:** `src/hooks/use-leads.tsx`

**Approach:** Keep context provider, add React Query for server state.
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const { data, isLoading, error, refetch } = useQuery({
  queryKey: ['leads'],
  queryFn: fetchLeads,
  staleTime: 30_000,
});
```

### Step 3: HIGH-040 + HIGH-041 — Type Safety & Icons
**Files:** `src/types/lead.ts`, `src/components/LeadDetailModal.tsx`, `src/components/enhanced/enhanced-lead-card.tsx`

**PRIORITY_ICON fix:**
```typescript
// Before: string mapping
export const PRIORITY_ICON: Record<LeadPriority, string> = {
  hot: 'Flame', warm: 'Sun', cold: 'Snowflake',
};

// After: typed component mapping
import { Flame, Sun, Snowflake, type LucideIcon } from 'lucide-react';
export const PRIORITY_ICON: Record<LeadPriority, LucideIcon> = {
  hot: Flame, warm: Sun, cold: Snowflake,
};
```

**getLucideIcon fix:**
```typescript
// Before: (LucideIcons as any)[name]
// After: Use direct icon imports or typed registry
```

### Step 4: HIGH-042 + HIGH-043 — API Route Fixes
**Files:** `src/app/api/leads/route.ts`, `src/app/api/lead/[id]/route.ts`

**`/api/leads`:** Already passes auth headers — verify.
**`/api/lead/[id]`:** Connect PATCH to real backend:
```typescript
export async function PATCH(request: NextRequest, { params }) {
  const { id } = await params;
  const backend = process.env.NEXT_PUBLIC_API_URL;
  const auth = request.headers.get('authorization');
  
  const body = await request.json();
  const res = await fetch(`${backend}/api/lead/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...(auth ? { Authorization: auth } : {}) },
    body: JSON.stringify(body),
  });
  
  if (!res.ok) return NextResponse.json({ error: 'Backend error' }, { status: res.status });
  return NextResponse.json(await res.json());
}
```

### Step 5: HIGH-044 — Division by Zero Guard
**File:** `src/components/enhanced/enhanced-command-center.tsx`

```typescript
const avgIntent = leads.length > 0
  ? (leads.reduce((sum, l) => sum + l.intentScore, 0) / leads.length).toFixed(1)
  : '0.0';
```

---

## Phase 4 Exit Criteria
- [ ] No raw `fetch` in hooks (all React Query)
- [ ] No memory leak warnings in React DevTools
- [ ] All interactive elements keyboard-accessible
- [ ] `npm run build` passes with `strict: true`

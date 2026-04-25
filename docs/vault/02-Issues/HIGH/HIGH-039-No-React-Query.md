---
severity: high
domain: frontend
status: resolved
phase: 4
file: src/hooks/use-leads.tsx
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-039: Migrate Hooks to React Query

## Location
[[The-Gallery]] → `src/hooks/use-leads.tsx`

## Description
The leads hook used raw `fetch` with `useEffect` + `useCallback`. No caching, no deduping, no background refetching, and manual error state management.

## Fix
Rewrote with `@tanstack/react-query`:
```typescript
const { data: leads = [], isLoading, error, refetch } = useQuery<Lead[], Error>({
  queryKey: ['leads'],
  queryFn: fetchLeads,
  staleTime: 30_000,
  refetchOnWindowFocus: false,
});

const updateMutation = useMutation({
  mutationFn: patchLead,
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ['leads'] }),
});
```

## Blast Radius
- `LeadProvider` still wraps everything (context preserved)
- All consumers get caching + deduping automatically
- New `updateLead` mutation for PATCH operations

## Verification
```typescript
// Network tab shows single request for multiple consumers
// Updating a lead invalidates cache and triggers refetch
```

## Related
- [[HIGH-042]] (API auth headers)
- [[HIGH-043]] (PATCH route)
- [[The-Gallery#Easels]]

## Commit
- `feat(frontend): migrate use-leads to React Query with mutations`

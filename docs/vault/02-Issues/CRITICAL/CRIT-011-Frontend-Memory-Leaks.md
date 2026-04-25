---
severity: critical
domain: frontend
status: open
phase: 1
file: src/hooks/use-auth.tsx, use-leads.tsx, use-profile.tsx
created: 2026-04-25
---

# CRIT-011: Frontend Memory Leaks

## Location
[[The-Gallery]] → `src/hooks/use-auth.tsx`, `src/hooks/use-leads.tsx`, `src/hooks/use-profile.tsx`

## Description
Async `useEffect` init functions are not cancellable. If the component unmounts while a request is in-flight, `setState` is called on an unmounted component. This causes memory leaks and React console warnings.

## Root Cause
Missing cleanup pattern (isMounted ref or AbortController) in async effects.

## Current Code (use-auth.tsx)
```typescript
useEffect(() => {
  async function init() {
    const refreshed = await refreshRequest();
    setUsername(decodeUsername(refreshed?.access_token));  // ← may call on unmounted
    setIsLoading(false);  // ← may call on unmounted
  }
  init();
}, []);  // ← no cleanup
```

## Fix
```typescript
useEffect(() => {
  let cancelled = false;
  async function init() {
    try {
      const refreshed = await refreshRequest();
      if (!cancelled) setUsername(decodeUsername(refreshed?.access_token));
    } finally {
      if (!cancelled) setIsLoading(false);
    }
  }
  init();
  return () => { cancelled = true; };
}, []);
```

## Blast Radius
- All 3 hooks affected
- 13+ components consume these hooks

## Verification
- Mount/unmount component rapidly → no console warnings

## Related
- [[CRIT-012]] Missing auth headers
- [[HIGH-037]] Auth no try/catch
- [[The-Gallery#Cracked-Frames]]

## Commit
`fix(frontend): add isMounted guard to all async hooks`

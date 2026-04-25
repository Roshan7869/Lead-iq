---
severity: high
domain: frontend
status: resolved
phase: 4
file: src/hooks/use-auth.tsx
line: 53-85
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-037: Auth Hook Error Swallowing

## Location
[[The-Gallery]] → `src/hooks/use-auth.tsx:53-85`

## Description
The `init()` function in `useAuth` caught errors with a bare `catch` and silently swallowed them. If token refresh or auth init failed, the error was invisible and `setIsLoading(false)` might not fire if an exception occurred in an unexpected place.

## Root Cause
- Bare `catch` with no error logging
- No `finally` block to guarantee `setIsLoading(false)`

## Fix
```typescript
// Before:
try { ... } catch { ... setIsLoading(false); }

// After:
try { ... } catch (err) {
  console.error('Auth init failed:', err);
  clearTokens();
  setUsername(null);
} finally {
  setIsLoading(false);
}
```

## Blast Radius
- Auth init failures are now visible in console
- Loading state always resolves (no infinite spinner)

## Verification
```typescript
// Throw in refreshRequest() during init
// → Console shows error, spinner stops
```

## Related
- [[HIGH-038]] (profile save errors)
- [[The-Gallery#Easels]]

## Commit
- `fix(frontend): add try/catch/finally to auth init`

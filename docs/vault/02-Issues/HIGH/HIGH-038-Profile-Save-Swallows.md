---
severity: high
domain: frontend
status: resolved
phase: 4
file: src/hooks/use-profile.tsx
line: 114-123
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-038: Profile Save Errors Not Surfaced

## Location
[[The-Gallery]] → `src/hooks/use-profile.tsx:114-123`

## Description
`saveProfile()` caught backend sync errors with `catch {}` and silently ignored them. The user saw `isSaving` toggle but had no way to know if the save actually succeeded.

## Root Cause
Empty catch block swallowed all errors.

## Fix
```typescript
// Before:
const saveProfile = useCallback(async (updates) => {
  ...
  try {
    await syncToBackend(next);
  } catch {}
  setIsSaving(false);
}, [profile]);

// After:
const saveProfile = useCallback(async (updates): Promise<{ success: boolean; error?: string }> => {
  ...
  try {
    await syncToBackend(next);
    return { success: true };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to save profile';
    console.error('Profile save failed:', message);
    return { success: false, error: message };
  } finally {
    setIsSaving(false);
  }
}, [profile]);
```

## Blast Radius
- Callers can now check `result.success`
- Context type updated to reflect new return type

## Verification
```typescript
const result = await saveProfile({ mode: 'hiring' });
if (!result.success) {
  toast.error(result.error);
}
```

## Related
- [[HIGH-037]] (auth hook errors)
- [[The-Gallery#Easels]]

## Commit
- `fix(frontend): surface profile save errors to callers`

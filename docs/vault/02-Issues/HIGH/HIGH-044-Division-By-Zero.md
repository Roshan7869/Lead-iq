---
severity: high
domain: frontend
status: resolved
phase: 4
file: src/components/enhanced/enhanced-command-center.tsx
line: 72
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-044: Division by Zero in Command Center

## Location
[[The-Gallery]] → `src/components/enhanced/enhanced-command-center.tsx:72`

## Description
`avgIntent` divided by `leads.length` without checking if the array was empty. When no leads existed, this produced `NaN`.

## Root Cause
Missing guard before division.

## Fix
```typescript
// Before:
const avgIntent = (leads.reduce((sum, l) => sum + l.intentScore, 0) / leads.length).toFixed(1);

// After:
const avgIntent = leads.length > 0
  ? (leads.reduce((sum, l) => sum + l.intentScore, 0) / leads.length).toFixed(1)
  : '0.0';
```

## Blast Radius
- Command center no longer shows `NaN` when empty
- Consistent fallback value of `'0.0'`

## Verification
```tsx
// Empty leads array
// Before: "Average Intent Score: NaN/10"
// After:  "Average Intent Score: 0.0/10"
```

## Related
- [[The-Gallery#Cracked Frames]]

## Commit
- `fix(frontend): guard division by zero in command center`

---
severity: high
domain: frontend
status: resolved
phase: 4
file: src/types/lead.ts
line: 130-134
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-040: Priority Icon Strings

## Location
[[The-Gallery]] → `src/types/lead.ts:130-134`

## Description
`PRIORITY_ICON` mapped priorities to strings like `'Flame'`, `'Sun'`, `'Snowflake'`. Components then tried to render these strings directly or pass them to a dynamic icon lookup. This produced raw text in the UI instead of actual icons.

## Root Cause
Icon mapping used string names instead of component references.

## Fix
```typescript
// Before:
export const PRIORITY_ICON: Record<LeadPriority, string> = {
  hot: 'Flame', warm: 'Sun', cold: 'Snowflake',
};

// After:
import { Flame, Sun, Snowflake, type LucideIcon } from 'lucide-react';
export const PRIORITY_ICON: Record<LeadPriority, LucideIcon> = {
  hot: Flame, warm: Sun, cold: Snowflake,
};
```

## Blast Radius
- All components using `PRIORITY_ICON` updated to render as JSX:
```tsx
const Icon = PRIORITY_ICON[lead.priority];
return Icon ? <Icon className="w-4 h-4" /> : null;
```

## Verification
```tsx
// Before: UI showed "Flame" as text
// After: UI shows actual flame icon
```

## Related
- [[HIGH-041]] (unsafe `as any` cast)
- [[The-Gallery#Canvases]]

## Commit
- `fix(frontend): map PRIORITY_ICON to LucideIcon components`

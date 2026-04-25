---
severity: high
domain: frontend
status: resolved
phase: 4
file: src/components/enhanced/enhanced-lead-card.tsx
line: 31-34
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-041: Unsafe `as any` Cast in Enhanced Lead Card

## Location
[[The-Gallery]] → `src/components/enhanced/enhanced-lead-card.tsx:31-34`

## Description
`getLucideIcon()` used `(LucideIcons as any)[name]` to dynamically look up icons. This bypasses TypeScript's type checking and can crash at runtime if the icon name doesn't exist.

## Root Cause
Dynamic import of `* as LucideIcons` with an `as any` cast.

## Fix
```typescript
// Before:
import * as LucideIcons from 'lucide-react';
const getLucideIcon = (name: string) => {
  const Icon = (LucideIcons as any)[name];
  return Icon ? <Icon className="w-4 h-4" /> : null;
};

// After:
import { Flame, Sun, Snowflake, Share2, Linkedin, Twitter, Zap, Cpu, User, Lightbulb, Handshake, Target, type LucideIcon } from 'lucide-react';

const ICON_REGISTRY: Record<string, LucideIcon> = {
  Flame, Sun, Snowflake, Share2, Linkedin, Twitter, Zap, Cpu,
  User, Lightbulb, Handshake, Target,
};

const getLucideIcon = (name: string): React.ReactElement | null => {
  const Icon = ICON_REGISTRY[name];
  return Icon ? <Icon className="w-4 h-4" /> : null;
};
```

## Blast Radius
- All icon lookups are now type-safe
- Unknown icon names return `null` instead of crashing

## Verification
```typescript
getLucideIcon('UnknownIcon'); // → null (no crash)
getLucideIcon('Flame');        // → <Flame className="w-4 h-4" />
```

## Related
- [[HIGH-040]] (priority icon strings)
- [[The-Gallery#Canvases]]

## Commit
- `fix(frontend): replace unsafe as any icon lookup with typed registry`

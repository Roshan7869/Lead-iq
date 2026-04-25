---
severity: critical
domain: frontend
status: open
phase: 1
file: tsconfig.json
created: 2026-04-25
---

# CRIT-013: TypeScript Strict Mode Disabled

## Location
[[The-Gallery]] → `tsconfig.json`

## Description
`"strict": false`, `"noImplicitAny": false`, `"strictNullChecks": false`. Type safety is severely disabled, allowing runtime bugs to compile without errors.

## Root Cause
TypeScript configured for leniency rather than safety.

## Current Code
```json
{
  "compilerOptions": {
    "strict": false,
    "noImplicitAny": false,
    "strictNullChecks": false,
    ...
  }
}
```

## Fix
```json
{
  "compilerOptions": {
    "strict": true,
    ...
  }
}
```

## Blast Radius
- **Entire `src/` codebase** — enabling strict will surface dozens/hundreds of type errors
- Must fix incrementally: start with `strictNullChecks`, then `noImplicitAny`, then full strict
- [[HIGH-040]] Priority icon strings — caught by strict type checking
- [[HIGH-041]] Unsafe `any` cast — caught by strict type checking

## Verification
```bash
npx tsc --noEmit → 0 errors
```

## Related
- [[HIGH-040]] Priority icon strings
- [[HIGH-041]] Unsafe any cast
- [[The-Gallery#Blank-Spaces]]

## Commit
`fix(frontend): enable TypeScript strict mode and fix type errors`

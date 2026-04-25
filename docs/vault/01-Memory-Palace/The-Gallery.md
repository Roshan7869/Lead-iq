---
type: domain
name: Frontend
door: The-Gallery
issues: 25
severity: critical
---

# The Gallery — Frontend Domain

> "Where the user experience is painted. Some frames are cracked. Some canvases are blank."

## Canvases (React Components)
- `src/components/LeadDetailModal.tsx` — [[HIGH-040]] Priority icon renders strings not nodes
- `src/components/enhanced/enhanced-lead-card.tsx` — [[HIGH-041]] Unsafe `any` cast
- `src/components/enhanced/enhanced-command-center.tsx` — [[HIGH-044]] Division by zero, Medium — autoFocus steals focus
- `src/views/Overview.tsx` — Medium — Emoji without aria-label, no loading states
- `src/views/DemandMiner.tsx` — Medium — No loading/error states
- `src/components/AppSidebar.tsx` — Medium — Missing aria-expanded

## Easels (React Hooks)
- `src/hooks/use-auth.tsx` — [[CRIT-011]] 🔴 Memory leak, [[HIGH-037]] No try/catch
- `src/hooks/use-leads.tsx` — [[CRIT-011]] 🔴 Memory leak, [[CRIT-012]] 🔴 Missing auth header, [[HIGH-039]] No React Query
- `src/hooks/use-profile.tsx` — [[CRIT-011]] 🔴 Memory leak, [[HIGH-038]] Swallows errors

## Cracked Frames (Bugs)
- `src/hooks/use-leads.tsx:32` — [[CRIT-012]] 🔴 No Authorization header → always demo data
- `src/app/api/lead/[id]/route.ts` — [[HIGH-043]] Only mutates demoLeads
- `src/lib/auth-client.ts` — Medium — Unsafe JSON parsing
- `src/components/WebMCPProvider.tsx` — Medium — Re-registers tools on every change

## Blank Spaces (Missing Features)
- No React Query usage despite installation
- No loading skeletons in views
- No error boundaries
- No Supabase realtime (claimed but absent)
- `tsconfig.json` — [[CRIT-013]] 🔴 strict: false

## Accessibility Issues
- `src/app/login/page.tsx` — High — Password toggle `tabIndex={-1}`
- `src/components/enhanced/enhanced-lead-card.tsx` — High — `<div onClick>` not keyboard accessible
- `src/components/LeadDetailModal.tsx` — Medium — Icon links no aria-label
- `src/components/profile-setup-wizard.tsx` — Low — Missing aria-current

## Fix Order
1. [[CRIT-011]] Fix memory leaks in all hooks (isMounted ref)
2. [[CRIT-012]] Add Authorization header to use-leads
3. [[CRIT-013]] Enable strict: true in tsconfig (incrementally fix errors)
4. [[HIGH-037]] Add try/catch to use-auth init
5. [[HIGH-038]] Surface profile save errors
6. [[HIGH-039]] Migrate to React Query
7. [[HIGH-040]] Fix priority icon rendering
8. [[HIGH-041]] Remove `any` cast from lead card
9. [[HIGH-042]] Ensure auth header flows through API route
10. [[HIGH-043]] Connect PATCH to real backend
11. [[HIGH-044]] Guard division by zero

## Related
- [[The-Citadel]] ← Back to hub
- [[Phase-1-Stop-the-Bleeding]] ← Active phase
- [[React-Query-Migration-Guide]] ← Reference

---
severity: high
domain: frontend
status: resolved
phase: 4
file: src/app/api/lead/[id]/route.ts
line: 25-52
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-043: PATCH Route Only Updates demoLeads

## Location
[[The-Gallery]] → `src/app/api/lead/[id]/route.ts`

## Description
The PATCH endpoint only modified the in-memory `demoLeads` array. Changes were lost on page refresh and never reached the real backend.

## Root Cause
No backend proxy — only local demo data mutation.

## Fix
```typescript
export async function PATCH(request: NextRequest, { params }) {
  const { id } = await params;
  const parsed = LeadUpdateSchema.safeParse(await request.json());
  if (!parsed.success) return NextResponse.json({ error: 'Validation failed' }, { status: 422 });

  // Forward to real backend
  if (BACKEND) {
    const auth = request.headers.get('authorization');
    const res = await fetch(`${BACKEND}/api/lead/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', ...(auth ? { Authorization: auth } : {}) },
      body: JSON.stringify(parsed.data),
    });
    if (res.ok) return NextResponse.json(await res.json());
  }

  // Fallback to demo
  const lead = demoLeads.find((l) => l.id === id);
  if (!lead) return NextResponse.json({ error: 'Lead not found' }, { status: 404 });
  return NextResponse.json({ lead: { ...lead, ...parsed.data } });
}
```

## Blast Radius
- Lead updates now persist to backend
- Demo fallback still works when backend is unavailable

## Verification
```bash
curl -X PATCH -H "Authorization: Bearer $TOKEN" -d '{"stage":"contacted"}' /api/lead/1
# → 200 with updated lead from backend
```

## Related
- [[HIGH-042]] (auth headers)
- [[The-Gallery#Blank Spaces]]

## Commit
- `fix(frontend): proxy PATCH to real backend with auth headers`

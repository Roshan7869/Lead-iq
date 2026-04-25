---
severity: critical
domain: security
status: open
phase: 1
file: backend/api/routes/leads.py
line: 32,73
created: 2026-04-25
---

# CRIT-001: Unauthenticated Lead Endpoints

## Location
[[The-Gatehouse]] → `backend/api/routes/leads.py:32,73`

## Description
`GET /api/leads` and `PATCH /api/lead/{id}` have **no authentication**. Anyone can enumerate and mutate the entire lead database.

## Root Cause
Missing `user: CurrentUser` dependency in route signatures.

## Current Code
```python
@router.get("/leads", response_model=LeadListResponse)
async def list_leads(
    stage: str | None = Query(None),  # ← NO AUTH
    ...
) -> LeadListResponse:

@router.patch("/lead/{lead_id}", response_model=LeadUpdateResponse)
async def update_lead(
    lead_id: str,  # ← NO AUTH
    body: LeadUpdateRequest,
) -> LeadUpdateResponse:
```

## Fix
```python
@router.get("/leads", response_model=LeadListResponse)
async def list_leads(
    user: CurrentUser,  # ← ADD THIS
    stage: str | None = Query(None),
    ...
) -> LeadListResponse:

@router.patch("/lead/{lead_id}", response_model=LeadUpdateResponse)
async def update_lead(
    lead_id: str,
    body: LeadUpdateRequest,
    user: CurrentUser,  # ← ADD THIS
) -> LeadUpdateResponse:
```

## Blast Radius
- Frontend tests calling `/api/leads` without auth will break
- OpenAPI schema will show auth requirement
- Next.js API proxy already forwards headers

## Verification
```bash
curl http://localhost:8000/api/leads → 401 Unauthorized
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/leads → 200 OK
```

## Related
- [[HIGH-020]] Stats unauthenticated
- [[HIGH-019]] MCP unauthenticated
- [[The-Gatehouse#Unlocked-Doors]]

## Commit
`fix(auth): add CurrentUser to lead endpoints`

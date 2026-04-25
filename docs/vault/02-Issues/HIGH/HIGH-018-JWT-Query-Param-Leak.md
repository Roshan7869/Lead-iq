---
severity: high
domain: security
status: resolved
phase: 2
file: backend/api/routes/auth.py
line: 88-101
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-018: JWT Query Param Leak

## Location
[[The-Gatehouse]] → `backend/api/routes/auth.py:88-101`

## Description
`GET /api/auth/me` accepted the JWT as a query parameter (`?token=...`). Query params are logged by proxies, browsers, and server access logs, creating a persistent credential leak.

## Root Cause
Route signature used `token: str = ""` instead of the standard `Authorization: Bearer` header.

## Fix
```python
# Before
@router.get("/me")
async def me(token: str = "") -> MeResponse:
    ...

# After
@router.get("/me")
async def me(user: OptionalUser) -> MeResponse:
    if not user:
        return MeResponse(username="", authenticated=False)
    return MeResponse(username=user, authenticated=True)
```

## Blast Radius
- Frontend must update any code passing `?token=` to `/auth/me`
- OpenAPI schema no longer shows `token` query param

## Verification
```bash
curl "http://localhost:8000/api/auth/me?token=xyz" → 401
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/auth/me → 200
```

## Related
- [[HIGH-047]] (JWT secret caching)
- [[CRIT-001]] (unauthenticated routes)
- [[The-Gatehouse#Guards]]

## Commit
- `fix(auth): remove JWT query param support from /me`

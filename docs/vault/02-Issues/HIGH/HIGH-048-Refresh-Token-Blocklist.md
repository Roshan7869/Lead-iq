---
severity: high
domain: security
status: resolved
phase: 2
file: backend/services/auth.py
line: new
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-048: No Refresh Token Revocation

## Location
[[The-Gatehouse]] → `backend/services/auth.py`

## Description
JWTs were stateless — logout was purely client-side. A stolen refresh token could be used indefinitely until it expired (30 days).

## Root Cause
No server-side tracking of revoked tokens.

## Fix
Added in-memory blocklist with safety cap:
```python
_token_blocklist: set[str] = set()
_BLOCKLIST_MAX_SIZE = 10_000

def revoke_token(token: str) -> None:
    if not token:
        return
    _token_blocklist.add(token)
    if len(_token_blocklist) > _BLOCKLIST_MAX_SIZE:
        half = sorted(_token_blocklist)[:_BLOCKLIST_MAX_SIZE // 2]
        _token_blocklist.difference_update(half)

def is_token_revoked(token: str) -> bool:
    return token in _token_blocklist
```

Also updated endpoints:
- `POST /auth/logout` now accepts `refresh_token` and revokes it
- `POST /auth/refresh` revokes the old refresh token after issuing a new pair
- `verify_token` checks blocklist for refresh tokens before decoding

## Blast Radius
- In-memory only → not shared across worker processes; production should back with Redis
- Frontend must send refresh token in logout body

## Verification
```bash
# Login → get refresh_token
REFRESH=$(curl -s -X POST http://localhost:8000/api/auth/login -d '{"username":"admin","password":"..."}' | jq -r .refresh_token)

# Refresh → old token revoked
curl -X POST http://localhost:8000/api/auth/refresh -d '{"refresh_token":"'$REFRESH'"}' → 200
# Second refresh with same token → 401 (revoked)
curl -X POST http://localhost:8000/api/auth/refresh -d '{"refresh_token":"'$REFRESH'"}' → 401
```

## Related
- [[HIGH-047]] (JWT secret caching)
- [[HIGH-018]] (JWT query param leak)
- [[The-Gatehouse#Lockbox]]

## Commit
- `feat(auth): add refresh token blocklist and revocation`

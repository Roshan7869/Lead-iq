---
severity: high
domain: security
status: resolved
phase: 2
file: backend/services/auth.py
line: 21-22
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-047: JWT Secret Cached at Module Level

## Location
[[The-Gatehouse]] → `backend/services/auth.py:21-22`

## Description
`_ALGORITHM = settings.JWT_ALGORITHM` and `_SECRET = settings.JWT_SECRET_KEY` were evaluated once at module import time. If `JWT_SECRET_KEY` was rotated in the environment, the running process continued using the old cached value.

## Root Cause
Module-level attribute eagerly evaluated settings.

## Fix
```python
# Removed module-level cache:
# _ALGORITHM = settings.JWT_ALGORITHM
# _SECRET    = settings.JWT_SECRET_KEY

# All functions now read settings dynamically:
jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
```

## Blast Radius
- Slightly more dictionary lookups per token operation (negligible)
- Secret rotation now takes effect immediately without restart

## Verification
```python
import os, backend.services.auth as auth
old_secret = auth.settings.JWT_SECRET_KEY
os.environ["JWT_SECRET_KEY"] = "rotated"
# auth.create_access_token("user") # now uses new secret
```

## Related
- [[HIGH-048]] (refresh token blocklist)
- [[HIGH-018]] (JWT query param leak)
- [[The-Gatehouse#Lockbox]]

## Commit
- `fix(auth): read JWT secret dynamically instead of caching at module level`

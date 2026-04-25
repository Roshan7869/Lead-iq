---
severity: high
domain: security
status: resolved
phase: 2
file: backend/shared/config.py
line: 71
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-016: Hardcoded Admin Username

## Location
[[The-Gatehouse]] → `backend/shared/config.py:71`

## Description
`ADMIN_USERNAME` defaulted to `"admin"`, making credential-stuffing attacks trivial even if the password is strong.

## Root Cause
Pydantic BaseSettings field with a default string value.

## Fix
```python
# Before
ADMIN_USERNAME: str = "admin"

# After
ADMIN_USERNAME: str
```

## Blast Radius
- All deployments must now explicitly set `ADMIN_USERNAME`
- Frontend login page assumes "admin" as default username — update hints if present

## Verification
```bash
python -c "from backend.shared.config import settings; print(settings.ADMIN_USERNAME)"
# Without env var → ValidationError (expected)
```

## Related
- [[HIGH-015]] (hardcoded DB password)
- [[The-Gatehouse#Lockbox]]

## Commit
- `fix(config): remove hardcoded ADMIN_USERNAME default`

---
severity: high
domain: security
status: resolved
phase: 2
file: backend/shared/config.py
line: 20
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-015: Hardcoded Database Password

## Location
[[The-Gatehouse]] → `backend/shared/config.py:20`

## Description
`DATABASE_URL` had a hardcoded default password `postgresql+asyncpg://leadiq:leadiq@localhost:5432/leadiq`. If deployed without overriding the env var, the database is exposed with a known default password.

## Root Cause
Pydantic BaseSettings field with a default string value instead of requiring it from environment.

## Fix
```python
# Before
DATABASE_URL: str = "postgresql+asyncpg://leadiq:leadiq@localhost:5432/leadiq"

# After
DATABASE_URL: str
```

## Blast Radius
- All deployments must now explicitly set `DATABASE_URL`
- Docker Compose and `.env.example` must be updated

## Verification
```bash
python -c "from backend.shared.config import settings; print(settings.DATABASE_URL)"
# Without env var → ValidationError (expected)
# With env var set → correct value
```

## Related
- [[HIGH-016]] (hardcoded admin username)
- [[The-Gatehouse#Lockbox]]

## Commit
- `fix(config): remove hardcoded DATABASE_URL default`

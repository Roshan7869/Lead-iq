---
severity: critical
domain: architecture
status: open
phase: 1
file: backend/api/routes/admin.py
line: 178-188
created: 2026-04-25
---

# CRIT-002: Deploy-Check Variable Shadowing Crash

## Location
[[The-Forge]] → `backend/api/routes/admin.py:178-188`

## Description
Inside the table-check loop, `result` (a `dict` defined at line 141) is reassigned to a SQLAlchemy `Result` object at line 183. On the **second iteration** of the loop, `result["checks"][...]` raises `TypeError: 'Result' object is not subscriptable`, crashing the endpoint.

## Root Cause
Variable shadowing — using the same name `result` for both the health dict and the SQLAlchemy query result.

## Current Code
```python
for table in tables:
    result = await session.execute(text(
        f"SELECT EXISTS (...) WHERE table_name = '{table}'"
    ))
    exists = result.scalar()
    result["checks"][f"table_{table}"] = "ok" if exists else "missing"  # CRASH on 2nd iter
```

## Fix
```python
for table in tables:
    table_result = await session.execute(text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :t)"
    ).params(t=table))
    exists = table_result.scalar()
    result["checks"][f"table_{table}"] = "ok" if exists else "missing"
```

## Blast Radius
- Localized to `deploy_check()` function only
- Also fixes [[CRIT-014]] SQL injection (same line)

## Verification
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/admin/deploy-check → 200 OK
# Verify all 4 tables are checked without crash
```

## Related
- [[CRIT-014]] SQL injection f-string (same code block)
- [[The-Forge#Broken-Gears]]

## Commit
`fix(admin): rename result variable to prevent shadowing crash`

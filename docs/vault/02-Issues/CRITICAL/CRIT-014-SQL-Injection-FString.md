---
severity: critical
domain: security
status: open
phase: 1
file: backend/api/routes/admin.py
line: 183
created: 2026-04-25
---

# CRIT-014: SQL Injection via f-string

## Location
[[The-Gatehouse]] → `backend/api/routes/admin.py:183`

## Description
`f"SELECT EXISTS (...) WHERE table_name = '{table}'"` uses Python f-string interpolation inside `sqlalchemy.text()`. While `table` is currently a hardcoded list, this pattern is dangerous and will be copied.

## Root Cause
Using f-string instead of SQLAlchemy bound parameters.

## Current Code
```python
result = await session.execute(text(
    f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
))
```

## Fix
```python
result = await session.execute(
    text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :t)").params(t=table)
)
```

## Blast Radius
- Localized to `deploy_check()` function
- Also fixes [[CRIT-002]] variable shadowing (same code block)

## Verification
```bash
# Verify no f-string SQL remains
grep -rn 'f"SELECT\|f"INSERT\|f"UPDATE\|f"DELETE' backend/api/routes/admin.py
# → Should return nothing
```

## Related
- [[CRIT-002]] Variable shadowing crash (same line)
- [[The-Gatehouse#Trapdoors]]

## Commit
`fix(security): use bound parameters instead of f-string SQL`

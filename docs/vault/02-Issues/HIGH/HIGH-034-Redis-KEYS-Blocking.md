---
severity: high
domain: pipeline
status: resolved
phase: 3
file: backend/services/velocity.py
line: 88-89
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-034: Redis KEYS Blocking Operation

## Location
[[The-Orrery]] → `backend/services/velocity.py:88-89`

## Description
`velocity_tracker.get_top_companies()` used `Redis.keys(pattern)` which is an O(N) blocking operation. On large Redis instances this blocks all clients for seconds.

## Root Cause
Convenience of `keys()` vs proper `scan_iter()`.

## Fix
```python
# Before:
keys = await self._client.keys(pattern)

# After:
keys = [k async for k in self._client.scan_iter(match=pattern)]
```

## Blast Radius
- All callers of `get_top_companies()` and MCP tools using it
- Redis monitor now shows `SCAN` not `KEYS`

## Verification
```bash
redis-cli MONITOR | grep -i keys
# Should show NO KEYS commands from the app
```

## Related
- [[HIGH-036]] (analyzer retry counter)
- [[The-Orrery#Gears]]

## Commit
- `fix(velocity): replace blocking KEYS with SCAN iterator`

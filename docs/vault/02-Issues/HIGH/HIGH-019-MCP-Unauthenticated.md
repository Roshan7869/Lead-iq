---
severity: high
domain: security
status: resolved
phase: 2
file: backend/api/mcp_server.py
line: 58-63
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-019: MCP Endpoint Unauthenticated in Dev Mode

## Location
[[The-Gatehouse]] → `backend/api/mcp_server.py:58-63`

## Description
`_verify_mcp_api_key()` returned `True` when `MCP_API_KEY` was empty, allowing unrestricted access in "dev mode." This meant any deployment missing the env var exposed all lead data via MCP tools.

## Root Cause
Dev-mode bypass was hardcoded in the helper function with no opt-out.

## Fix
```python
# Before
if not expected:
    return True  # No key configured → dev mode, allow all

# After
if not expected:
    return False  # No key configured → reject all requests
```

## Blast Radius
- All MCP tool calls now require a valid `MCP_API_KEY` header
- Frontend MCP clients must be updated to send the key

## Verification
```bash
curl http://localhost:8000/mcp > without key → 403
curl -H "X-MCP-API-Key: secret" http://localhost:8000/mcp → 200
```

## Related
- [[HIGH-020]] (stats unauthenticated)
- [[CRIT-001]] (unauthenticated routes)
- [[The-Gatehouse#Lockbox]]

## Commit
- `fix(mcp): remove empty-key dev mode bypass`

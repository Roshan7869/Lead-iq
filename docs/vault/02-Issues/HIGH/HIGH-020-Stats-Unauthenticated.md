---
severity: high
domain: security
status: resolved
phase: 2
file: backend/api/routes/stats.py
line: 19
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-020: Stats Endpoint Unauthenticated

## Location
[[The-Gatehouse]] → `backend/api/routes/stats.py:19`

## Description
`GET /api/stats/pipeline` had no authentication dependency, allowing anyone to enumerate lead counts, hot/warm breakdowns, and stream health.

## Root Cause
Missing `user: CurrentUser` in route signature.

## Fix
```python
@router.get("/pipeline", response_model=PipelineStatsResponse)
async def pipeline_stats(
    session: DbSession,
    stream: StreamClient,
    user: CurrentUser,
) -> PipelineStatsResponse:
```

## Blast Radius
- Dashboard widgets calling `/api/stats/pipeline` must include `Authorization` header
- OpenAPI schema now shows auth requirement

## Verification
```bash
curl http://localhost:8000/api/stats/pipeline → 401
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/stats/pipeline → 200
```

## Related
- [[CRIT-001]] (unauthenticated leads)
- [[HIGH-019]] (MCP unauthenticated)
- [[The-Gatehouse#Guards]]

## Commit
- `fix(auth): add CurrentUser to stats endpoint`

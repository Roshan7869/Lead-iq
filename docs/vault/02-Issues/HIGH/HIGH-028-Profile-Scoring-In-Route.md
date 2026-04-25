---
severity: high
domain: architecture
status: resolved
phase: 3
file: backend/api/routes/profile.py
line: 80-154
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-028: Profile Scoring Logic in Route

## Location
[[The-Forge]] → `backend/api/routes/profile.py:80-154`

## Description
`personalised_leads()` contained lead fetching, velocity batching, per-lead scoring, and ranking inline — 74 lines of business logic in a route.

## Root Cause
Business logic was written directly in route handlers.

## Fix
Extracted scoring logic to `backend/services/personalization.py::build_personalized_results()`:
```python
# New function in personalization.py
async def build_personalized_results(
    leads: list[Any],
    profile_data: dict[str, Any],
    velocity_map: dict[str, int],
    limit: int = 50,
) -> list[PersonalizedLeadOut]:
    ...

# Route after fix:
@router.get("/leads")
async def personalised_leads(...) -> list[PersonalizedLeadOut]:
    leads = await lead_repo.list_all(...)
    company_names = [l.company_name for l in leads if l.company_name]
    velocity_map = await velocity_tracker.get_velocity_map(company_names)
    return await build_personalized_results(leads, profile_data, velocity_map, limit)
```

## Blast Radius
- `personalization.py` grows by ~50 lines
- `profile.py` shrinks from 74 to 15 lines
- Scoring logic is now unit-testable

## Verification
```bash
python -m py_compile backend/services/personalization.py
python -m py_compile backend/api/routes/profile.py
```

## Related
- [[HIGH-027]] (pipeline logic in routes)
- [[The-Forge#Anvil]]

## Commit
- `refactor(routes): extract personalized scoring to personalization service`

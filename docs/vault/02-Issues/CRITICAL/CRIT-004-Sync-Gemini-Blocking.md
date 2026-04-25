---
severity: critical
domain: architecture
status: open
phase: 1
file: backend/llm/gemini_service.py
line: 110,208,242,308
created: 2026-04-25
---

# CRIT-004: Sync Gemini Calls Block Async Event Loop

## Location
[[The-Forge]] → `backend/llm/gemini_service.py`

## Description
Sync Vertex AI SDK calls (`model.generate_content()`, `model.get_embeddings()`) block the async event loop inside `async def` functions. This freezes the entire backend for seconds at a time.

## Root Cause
Calling sync blocking I/O directly inside async functions without `asyncio.to_thread()`.

## Affected Lines
- Line 110: `response = model.generate_content(...)`
- Line 208: `embeddings = model.get_embeddings(...)`
- Line 242: `response = model.generate_content(...)` (vision)
- Line 308: `response = model.generate_content(...)` (ICP)

## Fix
Wrap each sync call in `asyncio.to_thread()`:
```python
import asyncio

# Before:
response = model.generate_content(full_prompt, generation_config=...)

# After:
response = await asyncio.to_thread(
    model.generate_content, full_prompt, generation_config=...
)
```

## Blast Radius
- All 4 entry points in gemini_service.py
- `backend/workers/analyzer.py` (already wraps in asyncio.to_thread — follow same pattern)

## Verification
- Run analyzer worker → no event loop blocking warnings
- API response times remain stable during extraction

## Related
- [[The-Forge#Waterwheel]]
- [[backend/workers/analyzer.py]] (has correct pattern)

## Commit
`fix(llm): wrap sync Vertex AI calls in asyncio.to_thread`

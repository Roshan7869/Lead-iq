---
severity: high
domain: architecture
status: resolved
phase: 3
file: backend/llm/gemini_service.py
line: 137-145
created: 2026-04-25
resolved: 2026-04-25
---

# HIGH-035: Broad Exception Catch Returns Error Dicts

## Location
[[The-Forge]] → `backend/llm/gemini_service.py:137-145`

## Description
`extract_lead()`, `get_embedding()`, `extract_from_image()`, and `parse_natural_language_icp()` caught all exceptions and returned `{"error": ...}` dicts. Callers had no way to distinguish budget exceeded (expected) from API failure (unexpected).

## Root Cause
Error handling returned silent error dicts instead of raising exceptions.

## Fix
Added typed `GeminiExtractionError`:
```python
class GeminiExtractionError(Exception):
    def __init__(self, message: str, source: str | None = None, url: str | None = None):
        super().__init__(message)
        self.source = source
        self.url = url
```

All 4 functions now raise instead of returning error dicts:
- `extract_lead()` → `raise GeminiExtractionError(...)`
- `get_embedding()` → `raise GeminiExtractionError(...)`
- `extract_from_image()` → `raise GeminiExtractionError(...)`
- `parse_natural_language_icp()` → `raise GeminiExtractionError(...)`

## Blast Radius
- Callers must catch `GeminiExtractionError`
- `analyzer.py` updated to classify as permanent error
- No more silent error dict propagation

## Verification
```python
from backend.llm.gemini_service import GeminiExtractionError, extract_lead
try:
    await extract_lead("bad", "test", "http://x")
except GeminiExtractionError as e:
    print("Proper exception raised:", e)
```

## Related
- [[HIGH-036]] (analyzer retry counter)
- [[The-Forge#Furnace]]

## Commit
- `refactor(llm): raise GeminiExtractionError instead of returning error dicts`

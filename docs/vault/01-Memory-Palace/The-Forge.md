---
type: domain
name: Architecture
door: The-Forge
issues: 27
severity: critical
---

# The Forge — Architecture Domain

> "Where the machinery of the platform is built. The anvil is hot, but some gears are broken."

## Anvil (Core Services)
- `backend/llm/gemini_service.py` — [[CRIT-003]] 🔴 Broken confidence import, [[CRIT-004]] 🔴 Sync calls block event loop, [[HIGH-035]] Broad exception catch
- `backend/services/dedup_service.py` — [[CRIT-005]] 🔴 Imports deleted model
- `backend/services/confidence.py` — Canonical formula (no issues, but gemini_service imports from wrong path)

## Waterwheel (Async Event Loop)
- `backend/llm/gemini_service.py:110,208,242,308` — [[CRIT-004]] 🔴 Sync Vertex AI calls block loop
- `backend/events/emitter.py:33` — [[CRIT-009]] 🔴 Missing `await` on async Redis call
- `backend/workers/actors.py:91-97,130-136` — [[CRIT-010]] 🔴 `loop.run_until_complete()` crashes
- `backend/workers/pipeline.py:129-138` — [[HIGH-033]] Similar async anti-pattern

## Furnace (Scoring / ICP)
- `backend/services/confidence.py` — Canonical SOURCE_TRUST formula
- `backend/services/icp_service.py` — ICP NLP parser
- `backend/llm/gemini_service.py:341` — [[CRIT-003]] 🔴 Broken import prevents confidence computation

## Broken Gears (Bugs / Anti-Patterns)
- `backend/api/routes/admin.py:178-188` — [[CRIT-002]] 🔴 Variable shadowing crash
- `backend/api/routes/leads.py:101-149` — [[HIGH-027]] Logic in routes (fallback collection)
- `backend/api/routes/profile.py:80-154` — [[HIGH-028]] Scoring logic inline in route
- `backend/api/routes/leads.py:38-67` — [[HIGH-017]] Silent exception swallowing
- `backend/workers/analyzer.py:578-580` — [[HIGH-036]] Consumer no-ack on errors

## Fix Order
1. [[CRIT-002]] Fix deploy-check variable shadowing
2. [[CRIT-003]] Fix broken confidence import
3. [[CRIT-004]] Wrap sync Gemini calls in asyncio.to_thread()
4. [[CRIT-009]] Make emit() async with await
5. [[CRIT-010]] Fix Celery loop.run_until_complete() pattern
6. [[HIGH-027]] Move fallback logic to pipeline_service.py
7. [[HIGH-028]] Move profile scoring to personalization service
8. [[HIGH-033]] Fix DLQ signal handler async context
9. [[HIGH-034]] Replace Redis KEYS with SCAN
10. [[HIGH-035]] Raise GeminiExtractionError
11. [[HIGH-036]] Add retry counter to analyzer

## Related
- [[The-Citadel]] ← Back to hub
- [[The-Orrery]] ← Pipeline domain
- [[Phase-1-Stop-the-Bleeding]] ← Active phase

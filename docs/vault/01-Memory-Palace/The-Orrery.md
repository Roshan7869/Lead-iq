---
type: domain
name: Pipeline
door: The-Orrery
issues: 8
severity: critical
---

# The Orrery — Pipeline / Workers Domain

> "The celestial machine that moves data through the system. Some gears are stripped. Some orbits are broken."

## Gears (Celery Tasks)
- `backend/workers/pipeline.py` — [[CRIT-009]] 🔴 Calls sync emit(), [[HIGH-033]] DLQ signal handler async issue, [[HIGH-036]] Consumer no-ack
- `backend/workers/actors.py` — [[CRIT-010]] 🔴 `loop.run_until_complete()` crash pattern
- `backend/workers/analyzer.py` — [[HIGH-036]] Broad exception catch, no retry counter
- `backend/workers/scorer.py` — Calls sync emit() (will break when emit becomes async)

## Orbits (Data Flow)
1. Collection → `lead:collected` stream
2. Analysis → `lead:analyzed` stream
3. Scoring → `lead:scored` stream
4. Persistence → DB + `lead:ranked` stream
5. Outreach → `lead:outreach` stream

## Broken Links
- `backend/events/emitter.py:33` — [[CRIT-009]] 🔴 `emit()` is sync but calls async `_r.xadd()` without `await`. All domain events silently dropped.
- `backend/workers/pipeline.py:332-334` — Calls `emit()` synchronously inside async `_run()`. Will break when `emit` becomes async.
- `backend/workers/scorer.py:179` — Same issue.
- `backend/services/intent_monitor.py:207` — Same issue.

## Fix Order
1. [[CRIT-009]] Make emit() async with await
2. [[CRIT-010]] Fix Celery async anti-pattern
3. [[HIGH-033]] Fix DLQ signal handler
4. [[HIGH-036]] Add retry counter to analyzer

## Related
- [[The-Citadel]] ← Back to hub
- [[The-Forge]] ← Architecture domain
- [[Data-Flow-Pipeline]] ← Reference doc
- [[Phase-1-Stop-the-Bleeding]] ← Active phase

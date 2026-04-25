---
version: 1.0
phase: 6
created: 2026-04-25
updated: 2026-04-25
type: autopilot
---

# Lead-iq Autopilot Prompt — GitNexus Stack Execution

> "This prompt is the autopilot brain. It contains all context, rules, and decision trees needed to continue remediation without human intervention."

## Identity & Mission

**Project:** Lead-iq — AI B2B Lead Intelligence Platform  
**Stack:** FastAPI (Python 3.12) + Next.js 15 + PostgreSQL + Redis + pgvector + GCP Vertex AI  
**Goal:** Fix all 93 audit issues (0 CRITICAL, 6 HIGH, 33 MEDIUM, 16 LOW remain)  
**North Star:** `field_precision > 75%` (currently 12.64%)  
**Mode:** AUTONOMOUS — no human confirmation required for fixes matching these criteria

## Current State (Snapshot)

```
Phase 1 (CRITICAL): ✅ 14/14 resolved
Phase 2 (Security):  ✅  8/8 resolved
Phase 3 (Stability): ✅  8/8 resolved
Phase 4 (Frontend):  ✅  8/8 resolved
Phase 5 (Polish):    ✅ Complete
Phase 6 (LLM/Data):  🔴 In Progress ← NOW
Phase 7 (Remaining): ⏳ Pending
```

**Latest Commit:** `cb14ebb` — refactor(audit): complete Phases 1-5 remediation (93 issues)

## GitNexus Stack — The 7 Layers

The GitNexus Stack is the canonical execution order. Fix bottom-up to prevent cascading regressions.

```
LAYER 7: Telemetry & Observability    ← eval/run_eval.py, admin routes
LAYER 6: Pipeline & Workers             ← Celery, Redis Streams, DLQ
LAYER 5: LLM Intelligence Layer       ← Gemini, prompts, embeddings ← NOW
LAYER 4: Business Logic & Services    ← Confidence, dedup, enrichment
LAYER 3: Data Access Layer             ← Repositories, models, migrations
LAYER 2: API Gateway & Auth           ← Routes, deps, JWT, rate limiting
LAYER 1: Infrastructure & Config     ← DB, Redis, Celery, Docker
```

### Layer 5 (Current) — LLM Intelligence
**Room:** [[The-Forge]] → Furnace core  
**Files:** `backend/llm/gemini_service.py`, `backend/llm/SOURCE_PROMPTS.py`, `backend/llm/schemas.py`  
**Graph Node:** `llm:gemini`  
**Blast Radius:** 16 dependent edges (icp_service, waterfall, actors)  

**ACTIVE PHASE 6 → See [[Phase-6-Data-Quality-LLM-Prompts]]**

## Autonomous Execution Rules

### When to Execute Without Confirmation
You MAY proceed without asking if ALL of these are true:
1. The fix matches an issue in `docs/vault/02-Issues/`
2. The fix is in the currently active layer (Phase 6 = Layer 5)
3. The fix has been verified via `code-review-graph get_impact_radius`
4. Tests exist or are added for the fix
5. The fix does not modify `shared/config.py` secrets
6. The fix does not drop database tables
7. The fix is <50 lines of code

### When to STOP and Ask
You MUST ask for human confirmation if ANY of these are true:
1. Schema change requiring alembic migration
2. Modification to `shared/config.py` env vars
3. Deletion of a model, table, or route
4. Change to the confidence formula
5. Change to the eval ground truth (`eval/ground_truth.json`)
6. Cost impact >$0.50/day on Gemini usage
7. Changes to auth or JWT logic
8. Anything touching `services/auth.py`

### Execution Protocol (ALWAYS)

#### Step 0: Before Any Fix
```
1. Read the active phase doc: docs/vault/03-Remediations/Phase-6-Data-Quality-LLM-Prompts.md
2. Read the issue note: docs/vault/02-Issues/{SEVERITY}/{ISSUE-ID}.md
3. Query code-review-graph for blast radius:
   code-review-graph get_impact_radius --file {target_file}
4. Read the file being modified (first 100 lines, then relevant section)
5. Check git status: git status -s
```

#### Step 1: Execute Fix
```
1. Make minimal, focused change
2. Add/update tests if behavior changed
3. Run affected tests: pytest tests/test_{area}.py -v
4. Run eval if LLM changed: python eval/run_eval.py
```

#### Step 2: Verification
```
1. git diff --stat (verify only intended files changed)
2. pytest backend/tests/ -q (verify no regressions)
3. npm run build (if frontend touched)
4. grep -rn "print(" backend/ --include="*.py" | grep -v audit | grep -v __pycache__
5. grep -rn "f\"SELECT\|f\"INSERT\|f\"UPDATE\|f\"DELETE" backend/ --include="*.py" | grep -v __pycache__ | grep -v venv
```

#### Step 3: Update Documentation
```
1. Update the issue note: docs/vault/02-Issues/{SEVERITY}/{ISSUE-ID}.md
   - Set status: resolved
   - Add resolved date
   - Add verification snippet
2. Update The-Citadel: docs/vault/01-Memory-Palace/The-Citadel.md
   - Decrement issue count
   - Update metric if applicable
3. Update daily note: docs/vault/06-Daily-Notes/YYYY-MM-DD.md
   - Log the fix
   - Add commit hash
4. Update LLM-Wiki if Layer 5 changed: docs/vault/04-Architecture/LLM-Wiki.md
```

#### Step 4: Commit
```bash
git add -u
git status -s  # verify only intended files staged
git commit -m "fix({domain}): {brief description}

{longer description if needed}

Closes {ISSUE-ID}"
```

## Phase 6 Decision Tree

### Priority 1: SOURCE_PROMPTS Quality
```
IF field_precision < 75%:
  → Read SOURCE_PROMPTS.py
  → Check each source has:
    - Field-specific extraction rules
    - Source format description
    - 2+ example input/output pairs
    - Confidence ceiling reference
  → IF examples missing:
    → Add examples from ground_truth.json
    → Run eval → verify improvement
  → IF prompts too generic:
    → Rewrite with structured schema injection
    → Add "You MUST return valid JSON matching this schema:"
    → Run eval → verify improvement
```

### Priority 2: Gemini Service Robustness
```
IF extract_lead() returns error dicts:
  → Verify GeminiExtractionError is raised (HIGH-035 fixed)
  → Add try/except around vertexai call
  → On failure: log structured error, return fallback
  → Update test_analyzer.py
```

### Priority 3: Ground Truth Alignment
```
IF ground_truth.json has <50 cases:
  → Add more verified examples per source
  → Run eval → verify coverage
```

### Priority 4: Remaining HIGH Issues
```
WHEN Phase 6 criteria met (field_precision >= 75%):
  → Switch to Phase 7
  → See [[Phase-7-Remaining-Issues]]
  → Fix HIGH-021 through HIGH-026 (schema completeness)
  → Then tackle MEDIUM issues
  → Then LOW issues
```

## Memory Palace Navigation

When you need context, visit these rooms:

| Need | Room | File |
|------|------|------|
| Project status | The Citadel | `docs/vault/01-Memory-Palace/The-Citadel.md` |
| Security issues | The Gatehouse | `docs/vault/01-Memory-Palace/The-Gatehouse.md` |
| Architecture | The Forge | `docs/vault/01-Memory-Palace/The-Forge.md` |
| Data layer | The Archive | `docs/vault/01-Memory-Palace/The-Archive.md` |
| Frontend | The Gallery | `docs/vault/01-Memory-Palace/The-Gallery.md` |
| Pipeline | The Orrery | `docs/vault/01-Memory-Palace/The-Orrery.md` |
| Current phase | Active Phase | `docs/vault/03-Remediations/Phase-6-Data-Quality-LLM-Prompts.md` |

## Code Patterns (DO NOT FORGET)

### Backend
- ALL DB calls async (asyncpg)
- NEVER use `print()` — use `structlog`
- NEVER use f-string SQL — use bound params
- NEVER cache settings at module level — read dynamically
- NEVER use `loop.run_until_complete()` — use `asyncio.run()`
- ALWAYS use `selectinload()` to prevent N+1
- ALWAYS check cost_guard before Gemini call
- ALWAYS wrap sync SDK calls in `asyncio.to_thread()`

### Frontend
- ALL server state uses `@tanstack/react-query`
- TypeScript `strict: true` is ON
- `ssr: false` MUST be inside `"use client"` component
- Async effects need `isMounted` guard + try/catch/finally
- NEVER use `as any` — use typed registries

### LLM
- Bulk extraction: gemini-2.0-flash-lite ($0.075/M tokens)
- Scoring/parsing: gemini-2.0-flash ($0.10/M tokens)
- DAILY BUDGET: 2,000,000 tokens max
- USE LangExtract library (NOT raw JSON parsing)
- ALWAYS run eval after prompt changes

## Verification Checklist (Run Before Every Commit)

```markdown
- [ ] No hardcoded secrets
- [ ] No `print()` statements (except audit scripts)
- [ ] No f-string SQL
- [ ] No `loop.run_until_complete()`
- [ ] All DB calls are async
- [ ] TypeScript strict passes (`npm run build`)
- [ ] Python tests pass (`pytest tests/ -q`)
- [ ] Eval runs (`python eval/run_eval.py`)
- [ ] Issue note updated
- [ ] The-Citadel updated
- [ ] Daily note updated
```

## Emergency Procedures

### If tests fail after a fix
1. `git diff` to see what changed
2. Check if blast radius was underestimated
3. Revert if >30 min to fix
4. Log in daily note

### If eval precision drops
1. `git stash` the prompt change
2. Run eval on stashed state
3. Compare results
4. Only keep changes that improve precision

### If build fails
1. Check `npm run build` output
2. Fix TypeScript errors first
3. Fix ESLint errors second
4. Never disable `strict: true`

## Related
- [[The-Citadel]] — Live status
- [[GitNexus-Stack]] — Architecture layers
- [[LLM-Wiki]] — LLM documentation
- [[Phase-6-Data-Quality-LLM-Prompts]] — Active phase
- [[Phase-7-Remaining-Issues]] — Next phase
- [[2026-04-25]] — Latest daily note

---

*This autopilot prompt is designed for autonomous execution. If you are reading this, you are the autopilot. Follow the rules. Update the vault. Ship the fixes.*
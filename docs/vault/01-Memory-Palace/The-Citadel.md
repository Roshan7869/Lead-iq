---
type: hub
domains: 5
issues: 93
critical: 0
high: 6
medium: 33
low: 16
phase: 5
status: in-progress
---

# The Citadel — Lead-iq Project Hub

> "The fortress at the center of the memory palace. All roads lead here."

## North Star Metrics
| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| field_precision | >75% | 12.64% | 🔴 |
| email_validity | >70% | — | ⚪ |
| gemini_tokens_used | <2M/day | — | ⚪ |

## Sprint Progress
- [x] Days 0-6: Complete
- [x] Phase 1 (Stop the Bleeding): 14 CRITICAL resolved
- [x] Phase 2 (Security Hardening): 8 HIGH resolved
- [x] Phase 3 (Stability & Performance): 8 HIGH resolved
- [x] Phase 4 (Frontend Quality): 8 HIGH resolved
- [x] Phase 5 (Polish & Deploy): Complete
- [x] Days 7-13: In Progress
- [ ] Phase 6 (Data Quality & LLM Prompts): In Progress ← You are here

## The Memory Palace
Walk through each room to explore a domain. Each room contains artifacts (issues) to fix.

### 🏰 [[The-Gatehouse]] — Security Domain
*Guards, lockboxes, moats, and trapdoors.*
- **Artifacts:** [[CRIT-001]], [[CRIT-014]], [[HIGH-015]], [[HIGH-016]], [[HIGH-018]], [[HIGH-019]], [[HIGH-020]]
- **Status:** 2 critical, 5 high, 8 medium, 4 low

### ⚒️ [[The-Forge]] — Architecture Domain
*Anvils, waterwheels, furnaces, and broken gears.*
- **Artifacts:** [[CRIT-002]], [[CRIT-003]], [[CRIT-004]], [[CRIT-009]], [[CRIT-010]], [[HIGH-027]], [[HIGH-028]], [[HIGH-033]], [[HIGH-034]], [[HIGH-035]], [[HIGH-036]]
- **Status:** 4 critical, 10 high, 8 medium, 5 low

### 📜 [[The-Archive]] — Data Layer Domain
*Scrolls, index cards, missing pages, damaged bindings.*
- **Artifacts:** [[CRIT-005]], [[CRIT-006]], [[CRIT-007]], [[CRIT-008]], [[HIGH-021]], [[HIGH-022]], [[HIGH-023]], [[HIGH-024]], [[HIGH-025]], [[HIGH-026]], [[HIGH-029]], [[HIGH-030]]
- **Status:** 4 critical, 6 high, 7 medium, 3 low

### 🖼️ [[The-Gallery]] — Frontend Domain
*Canvases, easels, cracked frames, blank spaces.*
- **Artifacts:** [[CRIT-011]], [[CRIT-012]], [[CRIT-013]], [[HIGH-037]], [[HIGH-038]], [[HIGH-039]], [[HIGH-040]], [[HIGH-041]], [[HIGH-042]], [[HIGH-043]], [[HIGH-044]]
- **Status:** 3 critical, 8 high, 10 medium, 4 low

### 🔮 [[The-Orrery]] — Pipeline/Workers Domain
*Gears, orbits, broken links.*
- **Artifacts:** [[CRIT-009]], [[CRIT-010]], [[HIGH-033]], [[HIGH-036]]
- **Status:** 2 critical, 2 high

## The Map Room
- [[Dependency-Graph]] — Visual map of all imports and calls
- [[Data-Flow-Pipeline]] — Collection → Analysis → Scoring → Persistence
- [[Celery-Task-Topology]] — Task chains and beat schedule

## The Chronicle
- [[2026-04-25]] — Audit completed, vault established, Phase 1 & Phase 2 resolved

## Active Phase
→ [[Phase-6-Data-Quality-LLM-Prompts]] — Raise field_precision to >75%, audit SOURCE_PROMPTS, address remaining 55 issues

## Resources
- [[FastAPI-Patterns]]
- [[SQLAlchemy-Async-Patterns]]
- [[Celery-Async-Recipes]]
- [[React-Query-Migration-Guide]]
- [[TypeScript-Strict-Migration]]

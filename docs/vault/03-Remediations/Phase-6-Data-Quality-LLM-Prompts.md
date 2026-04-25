---
phase: 6
name: Data Quality & LLM Prompts
type: remediation
dependencies: [[Phase-5-Polish-Deploy]]
start_date: 2026-04-25
target_date: 2026-04-26
status: in-progress
---

# Phase 6: Data Quality & LLM Prompts (GitNexus Layer 5)

## Goal
Raise `field_precision` from 12.64% to >75% by rewriting SOURCE_PROMPTS and fixing extraction quality.

## GitNexus Stack Context
**Layer:** 5 (LLM Intelligence)  
**Room:** [[The-Forge]] (furnace core)  
**Blast Radius:** `backend/llm/gemini_service.py` → 16 dependent edges  
**Graph Query Before Fix:**
```bash
code-review-graph query --pattern "calls extract_lead"
code-review-graph get_impact_radius --file backend/llm/gemini_service.py
```

## Root Cause Analysis

### Current Precision Breakdown
| Source | Precision | Primary Failure |
|--------|-----------|---------------|
| github_profile | 15.71% | Missing company_name, industry |
| producthunt | 15.71% | Missing tech_stack, funding_stage |
| hacker_news | 15.00% | Missing email, company_size |
| tracxn | 8.75% | Missing almost all fields |
| yourstory | 8.00% | Missing almost all fields |

### Field-Level Failures
| Field | Precision | Notes |
|-------|-----------|-------|
| company_size | 50.00% | Best performing field |
| funding_stage | 32.00% | Partial extraction |
| location | 14.00% | Missing city/state parsing |
| company_name | 0.00% | NEVER extracted correctly |
| industry | 0.00% | NEVER extracted correctly |
| tech_stack | 0.00% | NEVER extracted correctly |
| email | 0.00% | NEVER extracted correctly |

### Diagnosis
1. **Prompts are too generic** — `SOURCE_PROMPTS` uses broad instructions without source-specific field mapping
2. **No structured output schema** — LLM returns freeform text, not guaranteed JSON
3. **No few-shot examples** — Prompts lack concrete extraction examples per source
4. **Regex fallback is too weak** — `regex_fallback_extract()` only captures basic patterns
5. **Ground truth mismatch** — Expected fields may not exist in source data

## Execution Plan

### Step 1: SOURCE_PROMPTS Audit (Hour 1)
**Files:** `backend/llm/SOURCE_PROMPTS.py`, `backend/llm/gemini_service.py`

For each source, verify:
- [ ] Field-specific extraction instructions exist
- [ ] Source format is described (HTML, API JSON, Markdown)
- [ ] Example input/output pairs included
- [ ] Confidence ceiling referenced (`SOURCE_TRUST`)

**Verification:**
```bash
grep -c "example" backend/llm/SOURCE_PROMPTS.py
grep -c "company_name" backend/llm/SOURCE_PROMPTS.py
grep -c "industry" backend/llm/SOURCE_PROMPTS.py
```

### Step 2: Add Pydantic Schema Enforcement (Hour 1)
**File:** `backend/llm/gemini_service.py`

Replace freeform JSON parsing with structured schema injection:
```python
from backend.llm.schemas import AnalyzedLead

# In extract_lead()
prompt = f"""
{SOURCE_PROMPTS[source]}

EXTRACT these fields as JSON matching this schema:
{AnalyzedLead.model_json_schema()}

SOURCE CONTENT:
{markdown_content}
"""
```

**Validation:**
- Parse with `AnalyzedLead.model_validate_json()`
- On validation error → log field-level failures
- Return partial results with confidence adjustment

### Step 3: Add Few-Shot Examples (Hour 2)
**File:** `backend/llm/SOURCE_PROMPTS.py`

Add 2-3 examples per source:
```python
EXAMPLES = {
    "github_profile": [
        {
            "input": "Google | github.com/google...",
            "output": {
                "company_name": "Google",
                "industry": "Technology",
                "tech_stack": ["Python", "Go", "TensorFlow"],
                "company_size": "10000+"
            }
        }
    ]
}
```

### Step 4: Improve Regex Fallback (Hour 1)
**File:** `backend/llm/gemini_service.py`

- Add domain-specific patterns per source
- Extract company name from title tags, h1, profile headers
- Extract industry from keywords, categories, tags

### Step 5: Run Eval & Iterate (Hour 2)
```bash
cd eval && python run_eval.py
```
Target: Each iteration must improve precision by >5%

### Step 6: Update LLM Wiki (Hour 0.5)
**File:** `docs/vault/04-Architecture/LLM-Wiki.md`
- Document new prompt patterns
- Add extraction example gallery
- Update confidence formula if changed

## Phase 6 Exit Criteria
- [ ] `field_precision >= 75%` (overall)
- [ ] `company_name` precision >= 60%
- [ ] `industry` precision >= 50%
- [ ] `email` precision >= 40%
- [ ] All SOURCE_PROMPTS have 2+ examples
- [ ] Gemini extraction uses Pydantic schema enforcement
- [ ] `python eval/run_eval.py` passes

## GitNexus Verification
After all changes:
```bash
# Verify no downstream breakage
code-review-graph detect_changes --from HEAD~1
# Check test coverage
code-review-graph query --pattern "tests_for extract_lead"
```

## Related
- [[GitNexus-Stack]] — Layer 5 context
- [[LLM-Wiki]] — Full LLM documentation
- [[Data-Flow-Pipeline]] — Where extracted data flows
- [[HIGH-035]] — GeminiExtractionError (already fixed)
- [[The-Forge]] — Memory Palace room for this domain
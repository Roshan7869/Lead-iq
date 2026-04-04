---
description: Full pre-deploy verification — never skip this before git push
---

Run checks in order. STOP at first ❌.

CHECK 1 — North star metrics:
  python eval/run_eval.py --quick
  ✅ field_precision >= 75%
  ✅ email_validity_rate >= 60%
  ❌ STOP if either below threshold

CHECK 2 — Pending migrations:
  alembic check
  ✅ No pending migrations
  ❌ Run: alembic revision --autogenerate + show me the file

CHECK 3 — All tests pass:
  pytest tests/ -v --tb=short -q
  ✅ 0 failures, 0 errors
  ❌ Show failing tests

CHECK 4 — No hardcoded secrets:
  grep -r "sk-" backend/ --include="*.py"
  grep -r "AIza" backend/ --include="*.py"
  grep -r "ghp_" backend/ --include="*.py"
  ✅ No matches
  ❌ Remove immediately

CHECK 5 — Routes registered:
  grep -r "include_router" backend/main.py
  All new routes present?

CHECK 6 — .env.example current:
  All env vars used in code present in .env.example?

CHECK 7 — Cost guard active:
  grep -r "check_budget" backend/llm/ --include="*.py"
  ✅ Every Gemini call wrapped in check_budget

CHECK 8 — LeadEvent logging:
  Every review inbox action calls log_lead_event()?

Report: ✅/❌ for each. Final: "SAFE TO DEPLOY" or "BLOCKED: [reason]"
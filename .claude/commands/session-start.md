---
description: Load full context, check metrics, set today's priority
---

Step 1 — Read CLAUDE.md completely. Do not skip any section.

Step 2 — Run these commands silently:
  git status
  git log --oneline -5
  alembic current
  cat TODO.md

Step 3 — Check north star metrics:
  python eval/run_eval.py --quick
  redis-cli get "gemini:tokens:$(date +%Y-%m-%d)"
  Show me the 3 metric scores.

Step 4 — IF any metric is failing (field_precision < 75% OR
  email_validity < 60%) → STOP. Tell me: "QUALITY FREEZE: [metric]
  is [value]. Fix this before building anything new."

Step 5 — Show me which CLAUDE.md sprint days are incomplete [ ].
  Recommend the single highest priority task for this session.

Step 6 — Ask: "Ready to build [task]? Or is there something else?"

DO NOT write any code. Just brief me.
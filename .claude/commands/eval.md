---
description: Run the Karpathy eval loop — measure, tune, commit only improvements
---

Action: $ARGUMENTS
(e.g., "tune tracxn prompt", "check all sources", "fix email extraction")

EVAL LOOP (follow exactly):

Step 1 — Run baseline:
  python eval/run_eval.py --source=$SOURCE
  Record current precision score.

Step 2 — Make ONE change only:
  - If tuning prompt: edit ONE entry in SOURCE_PROMPTS dict
  - If fixing extraction: change ONE function
  - NEVER change multiple things simultaneously

Step 3 — Run eval again:
  python eval/run_eval.py --source=$SOURCE
  Compare new score vs baseline.

Step 4 — Decision:
  IF new_score > baseline_score → keep change, show git diff
  IF new_score <= baseline_score → git checkout the changed file

Step 5 — Only commit when precision improves.
  git commit -m "eval: improve [source] precision [old]→[new]"

NEVER skip the eval run. NEVER commit without measuring.
This is the Karpathy ratchet — only improvements survive.
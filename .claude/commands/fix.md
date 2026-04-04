---
description: Diagnose and fix any error with full TDD cycle
---

Error to fix: $ARGUMENTS

Strict workflow:

Step 1 — READ before diagnosing.
  Read every file mentioned in the traceback.
  Read the failing test completely.
  Do NOT guess from the error message alone.

Step 2 — State root cause in exactly 2 sentences.
  Format: "The error is caused by [X]. The fix is [Y]."

Step 3 — Show fix in unified diff format:
  --- a/file.py
  +++ b/file.py
  @@ line numbers @@

Step 4 — If migration needed: show alembic revision command.
  Show generated migration file. Ask approval before running.

Step 5 — Run eval after fix:
  python eval/run_eval.py --quick
  Confirm no precision regression.

Step 6 — Update test to cover the fixed case.

DO NOT write code until you have read all relevant files.
DO NOT run alembic upgrade head — show command, I run it.
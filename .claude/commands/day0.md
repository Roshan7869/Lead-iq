---
description: Build the Day 0 foundation trinity — eval + cost guard + feedback model
---

This command scaffolds the 4 mandatory files before any feature work.

Read these existing files first (NO CODE YET):
  backend/models/lead.py
  backend/llm/ (all files)
  backend/database.py

Then build in this exact order:

TASK 1 — eval/ground_truth.json
Create 50 lead records, 10 per source:
Sources: tracxn, indimart, github_profile, yourstory, producthunt
Each record: { "source", "input_url", "expected": { all lead fields } }
Use realistic but fictional data. Show me the structure first.

TASK 2 — eval/run_eval.py
Script that:
  - Loads ground_truth.json
  - Calls each source's extractor with input_url
  - Compares output vs expected field-by-field
  - Prints: precision per field, precision per source, overall score
  - Accepts --quick flag (uses cached results, skips live scraping)
  - Accepts --source=tracxn flag (runs single source only)

TASK 3 — backend/llm/cost_guard.py
  check_budget(tokens_requested: int) → bool
  - Redis key: gemini:tokens:{date.today().isoformat()}
  - Daily limit: 2,000,000 tokens
  - If limit exceeded: log warning + return False
  - On True: increment Redis counter + set 86400 TTL

TASK 4 — backend/models/lead_event.py
SQLAlchemy model LeadEvent with columns:
  id UUID PK, lead_id FK→Lead, event_type Enum,
  field_name String nullable, original_value String nullable,
  corrected_value String nullable, time_to_decision Integer nullable,
  icp_id FK nullable, source_actor String nullable, created_at DateTime
Plus Alembic migration (SHOW command, do not run it)

Build one task at a time. Show complete file before writing it.
After all 4: run pytest tests/ -v and show results.
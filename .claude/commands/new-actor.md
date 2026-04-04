---
description: Scaffold a new data collector actor with Crawlee + LangExtract + eval
---

Create actor for source: $ARGUMENTS

Read these files first (NO CODE):
  workers/ (existing actor structure)
  backend/llm/gemini_service.py (SOURCE_PROMPTS dict)
  backend/workers/tasks.py (existing Celery tasks)
  eval/ground_truth.json (schema to match)

Then build in this order:

1. Add SOURCE_PROMPTS entry in gemini_service.py for $ARGUMENTS
   Write source-specific extraction instructions (not generic)
   Fields to focus on, vocabulary, confidence ceiling, gotchas

2. Create workers/$ARGUMENTS-actor/main.py:
   - Crawlee AsyncWebCrawler with stealth config
     (headless=True, user_agent_mode="random", simulate_user=True, magic=True)
   - fit_markdown=True in CrawlerRunConfig (LLM-ready output)
   - Call extract_lead(markdown, source="$ARGUMENTS", url=url)
   - Call compute_confidence(result, "$ARGUMENTS")
   - Call find_duplicate(lead) before save
   - Log with structlog — never print()

3. Create workers/$ARGUMENTS-actor/requirements.txt
   crawlee, playwright, pydantic, structlog, httpx

4. Add Celery task in backend/workers/tasks.py:
   @celery.task(bind=True, max_retries=3, default_retry_delay=60)
   async def scrape_$ARGUMENTS(self, url: str)

5. Register in backend/workers/registry.py

6. Add trigger endpoint in backend/routes/collectors.py:
   POST /api/collectors/$ARGUMENTS

7. Add 10 ground_truth entries for $ARGUMENTS to eval/ground_truth.json

8. Run: python eval/run_eval.py --source=$ARGUMENTS
   Show precision score. Tune SOURCE_PROMPTS until >70% precision.

IMPORTANT: Step 8 is NOT optional. Actor only ships when eval passes.
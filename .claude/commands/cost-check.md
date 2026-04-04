---
description: Check current GCP spend and Gemini token budget status
---

Run these checks:

1. Today's token usage:
   redis-cli get "gemini:tokens:$(date +%Y-%m-%d)"
   Show as: [used] / 2,000,000 tokens ([%] of daily budget)

2. Calculate estimated daily cost:
   Flash-Lite: used_tokens / 1,000,000 * 0.075
   Show: "Estimated today: $X.XX"

3. Extrapolate monthly burn:
   daily_cost * 30
   Compare to $300 trial credit (90 days)
   Show: "At this rate, $300 credit lasts [N] days"

4. Check Redis quota counters:
   redis-cli get "quota:newsapi:$(date +%Y-%m-%d)"
   redis-cli get "quota:hunter:$(date +%Y-%m-%d)"
   redis-cli get "quota:github:$(date +%Y-%m-%d)"
   Show remaining per API.

5. If daily token usage > 1,500,000 (75% of budget):
   WARN: "Approaching budget limit. Consider batching extractions."

6. If any free API quota exhausted:
   WARN: "[API] quota exhausted for today. Will resume at midnight UTC."
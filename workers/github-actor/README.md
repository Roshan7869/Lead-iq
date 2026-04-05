"""
workers/github-actor/README.md — GitHub Collector Actor

This actor collects GitHub user and organization profiles and enqueues them
to the LeadIQ pipeline for analysis.

## Overview

The GitHub collector:
- Fetches GitHub profiles via the GitHub API
- Aggregates technology stack from repositories
- Enqueues profiles to the pipeline's Redis stream
- Handles rate limiting with exponential backoff

## Architecture

```
Celery Task: actors.collect_github(username)
    ↓
GitHubCollector.fetch_profile(username)
    ↓
GitHubCollector.fetch_repos(username)
    ↓
GitHubCollector.aggregate_tech_stack(repos)
    ↓
GitHubCollector.to_pipeline_message(profile, repos, tech_stack)
    ↓
redis.xadd("lead:collected", message)
    ↓
Pipeline picks up: run_analysis_consumer() → GeminiAnalyzer
    ↓
AnalysisResult → score_opportunity() → persist
```

## Quota

- **Authenticated (GITHUB_TOKEN)**: 5000 requests/hour
- **Anonymous**: 60 requests/hour

The actor tracks usage in Redis: `quota:github:{date}`

## Usage

### As a Celery Task

The task is registered in `backend/workers/actors.py`:

```python
@app.task(name="actors.collect_github")
def collect_github(username: str):
    ...
```

Run manually:
```bash
celery -A backend.workers.pipeline worker --loglevel=info
```

Trigger the task:
```python
from backend.workers.actors import collect_github
collect_github.delay("Roshan7869")
```

### Direct Usage

```python
from workers.github_actor.main import GitHubCollector
from backend.shared.stream import redis_stream

collector = GitHubCollector(redis_stream._r)
result = await collector.collect_profile("Roshan7869", "lead:collected")
print(result)
```

## Environment Variables

- `GITHUB_TOKEN`: GitHub personal access token (recommended)
- `PIPELINE_STREAM_KEY`: Redis stream to enqueue to (default: "lead:collected")

## API Endpoints

### POST /api/collectors/github

Collect a GitHub profile or search for India founders.

```bash
# Collect single profile
curl -X POST http://localhost:8000/api/collectors/github \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"mode": "profile", "username": "Roshan7869"}'

# Search for India founders
curl -X POST http://localhost:8000/api/collectors/github \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"mode": "search", "tech_stack": ["python", "react"], "location": "India"}'
```

## Rate Limiting

- Profile collection: 10 requests/hour
- Search: 5 requests/hour

## Testing

```bash
python -m pytest tests/test_github_collector.py -v
```

## Monitors

The actor is controlled by feature flags in Redis:
- `actors:github:enabled` (default: 1 = enabled)
- `actors:telegram:enabled` (default: 1 = enabled)

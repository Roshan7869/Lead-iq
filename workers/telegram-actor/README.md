"""
workers/telegram-actor/README.md — Telegram Collector Actor

This actor scrapes public Telegram channels for funding/hiring signals
and enqueues them to the LeadIQ pipeline for analysis.

## Overview

The Telegram collector:
- Scrapes t.me/s/{channel} public preview HTML (no bot token required)
- Filters messages for funding or hiring signals
- Enqueues qualifying messages to the pipeline's Redis stream
- Tracks watermarks to avoid reprocessing old messages

## Architecture

```
Celery Task: actors.monitor_telegram(channels)
    ↓
TelegramCollector.run_all(pipeline_stream)
    ↓
for each channel:
    TelegramCollector.collect_channel(channel, pipeline_stream)
        ↓
    TelegramCollector.fetch_channel_messages(channel)
        ↓
    TelegramCollector.should_process(text) → (True, "funding")
        ↓
    TelegramCollector.to_pipeline_message(message, signal_type)
        ↓
    redis.xadd("lead:collected", message)
        ↓
    Pipeline picks up: run_analysis_consumer() → GeminiAnalyzer
        ↓
    AnalysisResult → score_opportunity() → persist
```

## Signal Types

### Funding Signals (T1 - single match required)
- "raises", "raised", "funding", "series a/b/c", "seed round", "pre-seed"
- "crore", "million", "billion"
- "backed by", "investment", "valuation", "unicorn"

### Hiring Signals (T2 - need 2+ matches)
- "hiring", "we're growing", "join our team", "open position"
- "we're looking for", "new opening", "we are hiring"

## Quota

- **Requests**: 500/day per actor (tracked in Redis: `quota:telegram:{date}`)
- **Watermarks**: 7 days TTL in Redis

## Usage

### As a Celery Task

The task is registered in `backend/workers/actors.py`:

```python
@app.task(name="actors.monitor_telegram")
def monitor_telegram(channels: list[str] | None = None):
    ...
```

Run manually:
```bash
celery -A backend.workers.pipeline worker --loglevel=info
```

Trigger the task:
```python
from backend.workers.actors import monitor_telegram
monitor_telegram.delay()
```

### Direct Usage

```python
from workers.telegram_actor.main import TelegramCollector
from backend.shared.stream import redis_stream

collector = TelegramCollector(redis_stream._r)
result = await collector.run_all("lead:collected")
print(result)
```

## Environment Variables

- `TELEGRAM_WATCHED_CHANNELS`: Comma-separated public channel usernames
  - Default: "@inc42,@startupsindia,@yourstory"
- `PIPELINE_STREAM_KEY`: Redis stream to enqueue to (default: "lead:collected")

## API Endpoints

### GET /api/collectors/telegram/watermarks

Returns current watermark for each watched channel:
```json
{
  "@inc42": 101,
  "@startupsindia": 203,
  "@yourstory": 345
}
```

### POST /api/collectors/telegram

Manually trigger Telegram monitoring:
```bash
curl -X POST http://localhost:8000/api/collectors/telegram \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"channels": ["@inc42", "@startupsindia"], "force_refetch": false}'
```

## Watermarks

Each channel's last processed message ID is stored in Redis:
```
Key: telegram:watermark:{channel_name}
Value: message_id (int)
```

This ensures only new messages are processed on each run.

## Testing

```bash
python -m pytest tests/test_telegram_collector.py -v
```

## Monitors

The actor is controlled by feature flags in Redis:
- `actors:telegram:enabled` (default: 1 = enabled)

## Scheduling

Runs every 2 hours via Celery Beat:
```python
"telegram-monitor": {
    "task": "actors.monitor_telegram",
    "schedule": crontab(hour="*/2"),  # Every 2 hours
    "options": {"queue": "monitoring"},
}
```

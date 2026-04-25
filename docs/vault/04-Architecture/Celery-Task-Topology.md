---
type: architecture
name: Celery Task Topology
tasks: 8
chains: 3
---

# Celery Task Topology

## Task Definitions

| Task | File | Queue | Bind | Retries |
|------|------|-------|------|---------|
| `collect_and_publish` | `pipeline.py` | default | False | 3 |
| `run_analysis_consumer` | `pipeline.py` | default | False | 3 |
| `run_scoring_consumer` | `pipeline.py` | default | False | 3 |
| `persist_scored_leads` | `pipeline.py` | default | False | 3 |
| `refresh_intent_signals` | `pipeline.py` | default | True | 3 |
| `compute_daily_metrics` | `pipeline.py` | default | True | 3 |
| `process_dlq_retries` | `pipeline.py` | default | True | 3 |
| `dedup_lead` | `pipeline.py` | default | False | 3 |

## Actor Tasks

| Task | File | Soft Limit | Hard Limit |
|------|------|------------|------------|
| `actors.collect_github` | `actors.py` | 300s | 360s |
| `actors.search_github_india` | `actors.py` | 300s | 360s |
| `actors.monitor_telegram` | `actors.py` | 600s | 720s |

## Task Chains

### Chain 1: Full Pipeline
```
collect_and_publish
  → run_analysis_consumer
    → run_scoring_consumer
      → persist_scored_leads
```

### Chain 2: Actor Discovery
```
search_github_india
  → [spawns] collect_github (per user)
```

### Chain 3: Retry Loop
```
process_dlq_retries (every 5 min)
  → dedup_lead (for retried records)
```

## Beat Schedule

```python
celery_app.conf.beat_schedule = {
    "collect-every-15-min": {
        "task": "pipeline.collect_and_publish",
        "schedule": 900.0,
    },
    "refresh-intent-every-30-min": {
        "task": "pipeline.refresh_intent_signals",
        "schedule": 1800.0,
    },
    "daily-metrics-at-midnight": {
        "task": "pipeline.compute_daily_metrics",
        "schedule": crontab(hour=0, minute=0),
    },
    "dlq-retry-every-5-min": {
        "task": "pipeline.process_dlq_retries",
        "schedule": 300.0,
    },
    "telegram-monitor-every-2-hours": {
        "task": "actors.monitor_telegram",
        "schedule": 7200.0,
    },
}
```

## Signal Handlers

| Signal | Handler | Purpose |
|--------|---------|---------|
| `task_failure` | `on_pipeline_task_failure` | Write to DLQ |
| `task_retry` | `on_pipeline_task_retry` | Log retry attempt |

## DLQ Integration

```python
# pipeline.py lines 29-64
@task_failure.connect
def on_pipeline_task_failure(sender, task_id, exception, args, kwargs, **extras):
    # Writes failed task to LeadDLQ table
    # Exponential backoff: 2h, 4h, 8h
```

## Related
- [[Data-Flow-Pipeline]] — Stage-by-stage data flow
- [[GitNexus-Stack]] — Layer 6
- [[The-Orrery]] — Memory Palace room

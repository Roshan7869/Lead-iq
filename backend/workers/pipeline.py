"""
workers/pipeline.py — Celery app + task chain + collection orchestration.

Task chain topology:
  collect_all_sources → [dedup + persist posts] → analyze_post → score_post → notify

Celery app uses Redis as both broker and result backend.
Consumer groups ensure at-least-once delivery without double-processing.
"""
from __future__ import annotations

import asyncio
import uuid
import datetime as dt
from typing import Any

from celery import Celery
from celery.utils.log import get_task_logger

from backend.shared.config import settings

logger = get_task_logger(__name__)

# ── Celery app ────────────────────────────────────────────────────────────────

celery_app = Celery(
    "leadiq",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "backend.workers.pipeline",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,           # Don't ack until task completes
    worker_prefetch_multiplier=1,  # One task at a time per worker (IO-heavy)
    # Worker resource management
    worker_concurrency=3,
    worker_max_tasks_per_child=100,
    beat_schedule={
        "collect-every-15-min": {
            "task": "backend.workers.pipeline.collect_and_publish",
            "schedule": 900.0,     # 15 minutes
        },
        "intent-refresh-every-30-min": {
            "task": "backend.workers.pipeline.refresh_intent_signals",
            "schedule": 1800.0,    # 30 minutes
        },
        "daily-metrics-at-midnight": {
            "task": "backend.workers.pipeline.compute_daily_metrics",
            "schedule": 0.0,       # Midnight UTC (crontab: 0 0 * * *)
            "options": {"queue": "metrics"},
        },
    },
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_async(coro) -> Any:
    """Run an async coroutine from a sync Celery task."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


# ── Tasks ─────────────────────────────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def collect_and_publish(self) -> dict[str, Any]:
    """
    Main collection task: runs all collectors, deduplicates, publishes to lead:collected.
    Scheduled by Celery Beat every 15 minutes.
    """
    async def _run() -> dict[str, Any]:
        from backend.shared.stream import redis_stream
        from backend.shared.deduper import PostDeduplicator
        from backend.ingestion.orchestrator import IngestionOrchestrator
        from backend.ingestion.collectors import get_collectors

        await redis_stream.connect()

        # ── Load active user profile for adaptive collection ─────────────────
        profile_mode    = "b2b_sales"
        include_keywords: list[str] = []
        exclude_keywords: list[str] = []

        try:
            from backend.shared.db import get_db_session
            from backend.shared.repository import ProfileRepo
            from backend.services.personalization import (
                QueryGenerator, passes_keyword_filter
            )
            async with get_db_session() as session:
                profile = await ProfileRepo(session).get_active()
                if profile:
                    profile_mode     = profile.mode or "b2b_sales"
                    include_keywords = profile.include_keywords or []
                    exclude_keywords = profile.exclude_keywords or []

                    qg = QueryGenerator()
                    reddit_queries = qg.generate_reddit_queries(
                        mode=profile_mode,
                        include_keywords=include_keywords,
                        target_industries=profile.target_industries or [],
                        hiring_roles=profile.hiring_roles or [],
                        skills=profile.skills or [],
                    )
                    reddit_subs = qg.generate_subreddits(
                        mode=profile_mode,
                        target_industries=profile.target_industries or [],
                    )
                    reddit_collector = RedditCollector(
                        subreddits=reddit_subs,
                        search_queries=reddit_queries,
                    )
                else:
                    reddit_collector = RedditCollector()
        except Exception as exc:
            logger.warning("Profile load failed, using defaults: %s", exc)
            reddit_collector = RedditCollector()

        # Use the ingestion orchestrator for unified collection
        orchestrator = IngestionOrchestrator()
        result = await orchestrator.run_all()

        logger.info("Collection run complete: %d published, %d skipped", result["published"], result["skipped"])
        return {
            "published": result["published"],
            "skipped":   result["skipped"],
            "mode":      profile_mode,
            "failed":    result.get("failed", 0),
            "timestamp": dt.datetime.now(dt.UTC).isoformat(),
        }

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.error("collect_and_publish failed: %s", exc)
        raise self.retry(exc=exc) from exc


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def run_analysis_consumer(self) -> dict[str, Any]:
    """
    Long-running task: consumes lead:collected, runs GeminiAnalyzer, publishes to lead:analyzed.
    """
    async def _run() -> dict[str, Any]:
        from backend.shared.stream import redis_stream
        from backend.workers.analyzer import run_analyzer

        await redis_stream.connect()
        consumer_name = f"analyzer-{uuid.uuid4().hex[:8]}"
        await run_analyzer(consumer_name=consumer_name)
        return {"consumer": consumer_name}

    return _run_async(_run())


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def run_scoring_consumer(self) -> dict[str, Any]:
    """
    Long-running task: consumes lead:analyzed, scores, publishes to lead:scored.
    """
    async def _run() -> dict[str, Any]:
        from backend.shared.stream import redis_stream
        from backend.workers.scorer import run_scorer

        await redis_stream.connect()
        consumer_name = f"scorer-{uuid.uuid4().hex[:8]}"
        await run_scorer(consumer_name=consumer_name)
        return {"consumer": consumer_name}

    return _run_async(_run())


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def persist_scored_leads(self) -> dict[str, Any]:
    """
    Consume lead:scored stream and persist qualifying leads to PostgreSQL.
    Only persists leads with final_score >= 40 (cool or above).
    Emits domain events for lead_created, lead_enriched, and lead_scored.
    """
    async def _run() -> dict[str, Any]:
        from backend.shared.db import get_db_session
        from backend.shared.repository import LeadRepo, PostRepo
        from backend.shared.stream import redis_stream
        from backend.events.emitter import emit

        await redis_stream.connect()
        group = "persisters"
        stream = settings.STREAM_SCORED
        await redis_stream.ensure_group(stream, group)

        consumer_name = f"persister-{uuid.uuid4().hex[:8]}"
        events = await redis_stream.consume_group(
            stream,
            group,
            consumer_name,
            count=20,
            block_ms=5000,
        )

        persisted = 0
        for event in events:
            try:
                final_score = float(event.get("final_score", 0.0))
                if final_score < 40.0:
                    await redis_stream.ack(stream, group, event.event_id)
                    continue

                async with get_db_session() as session:
                    post_repo = PostRepo(session)
                    lead_repo = LeadRepo(session)

                    # Upsert the raw post
                    content_hash = event.get("content_hash", "")
                    if not await post_repo.exists_by_hash(content_hash):
                        post = await post_repo.create({
                            "source": event.get("source", ""),
                            "external_id": event.get("external_id", str(uuid.uuid4())),
                            "url": event.get("url", ""),
                            "title": event.get("title", ""),
                            "body": event.get("body", ""),
                            "author": event.get("author", ""),
                            "score": int(float(event.get("score", 0))),
                            "content_hash": content_hash,
                            "raw_meta": event.get("raw_meta", {}),
                        })
                        post_id = post.id
                    else:
                        post_id = None

                    # Upsert the lead
                    await lead_repo.upsert({
                        "post_id": post_id,
                        "is_opportunity": bool(event.get("is_opportunity", False)),
                        "confidence": float(event.get("confidence", 0.0)),
                        "intent": event.get("intent", "other"),
                        "urgency": event.get("urgency", "low"),
                        "opportunity_score": float(event.get("opportunity_score", 0.0)),
                        "icp_fit_score": float(event.get("icp_fit_score", 0.0)),
                        "final_score": final_score,
                        "score_band": event.get("score_band", "cold"),
                        "company_name": event.get("company_name"),
                        "company_size": event.get("company_size"),
                        "industry": event.get("industry"),
                        "contact_name": event.get("contact_name"),
                        "contact_title": event.get("contact_title"),
                        "outreach_draft": event.get("outreach_draft"),
                        "analyzed_at": dt.datetime.now(dt.UTC),
                        "scored_at": dt.datetime.now(dt.UTC),
                    })
                    persisted += 1
                    lead_id = event.get("id", str(uuid.uuid4()))

                    # Emit domain events
                    emit("lead_created", {"id": lead_id, "source": event.get("source")})
                    emit("lead_enriched", {"id": lead_id, "company_name": event.get("company_name")})
                    emit("lead_scored", {"id": lead_id, "final_score": final_score, "score_band": event.get("score_band")})

                await redis_stream.ack(stream, group, event.event_id)
            except Exception as exc:
                logger.error("Persist failed for event %s: %s", event.event_id, exc)

        logger.info("Persisted %d leads", persisted)
        return {"persisted": persisted}

    return _run_async(_run())


# ── Intent Signal Refresh Task ────────────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def refresh_intent_signals(self) -> dict[str, Any]:
    """
    Refresh intent signals for stale leads.
    Scheduled by Celery Beat every 30 minutes.

    Checks:
        - NewsAPI for recent news
        - GitHub hiring signals
        - Updates signal scores with temporal decay
    """
    async def _run() -> dict[str, Any]:
        from backend.services.intent_monitor import refresh_intent_signals

        try:
            await refresh_intent_signals(limit=10)
            return {"status": "completed", "timestamp": dt.datetime.now(dt.UTC).isoformat()}
        except Exception as exc:
            logger.error("intent_refresh_failed: %s", exc)
            raise self.retry(exc=exc) from exc

    return _run_async(_run())


# ── Daily Metrics Task ────────────────────────────────────────────────────────────

@celery_app.task(bind=True)
def compute_daily_metrics(self) -> dict[str, Any]:
    """
    Compute and log daily metrics.
    Scheduled by Celery Beat at midnight UTC.

    Metrics:
        - leads_extracted: Count of new leads today
        - email_validity_rate: % of valid emails
        - field_precision: Eval score against ground truth
        - dedup_rate: Duplicate collision rate
        - gemini_tokens_used: Token consumption
        - budget_remaining: Remaining GCP budget
    """
    async def _run() -> dict[str, Any]:
        from datetime import date
        from backend.llm.cost_guard import get_budget_status
        from backend.shared.stream import redis_stream

        await redis_stream.connect()
        r = redis_stream._r

        today = date.today().isoformat()

        # Token usage
        budget_status = await get_budget_status()

        # Lead counts
        leads_collected = int(r.get(f"leads:collected:{today}") or 0)
        leads_deduped = int(r.get(f"leads:deduped:{today}") or 0)

        metrics = {
            "date": today,
            "leads_collected": leads_collected,
            "leads_deduped": leads_deduped,
            "tokens_used": budget_status["used"],
            "tokens_remaining": budget_status["remaining"],
            "budget_percent_used": budget_status["percent_used"],
        }

        # Quality freeze check
        # TODO: Get email_validity_rate from LeadEvent aggregation
        # if email_validity_rate < 0.60:
        #     metrics["quality_freeze"] = True
        #     logger.error("QUALITY_FREEZE_TRIGGERED", validity=email_validity_rate)
        #     # TODO: Pause all actors

        logger.info("daily_metrics", **metrics)

        # Post to Sentry
        try:
            import sentry_sdk
            sentry_sdk.capture_message("daily_metrics", extras=metrics)
        except ImportError:
            pass

        return metrics

    return _run_async(_run())


# ── Dedup Task ─────────────────────────────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def dedup_lead(self, lead_id: str) -> dict[str, Any]:
    """
    Deduplicate a single lead after insertion.

    Runs 3-tier dedup:
        1. Exact match on email/linkedin/domain
        2. Fuzzy match on company name
        3. Vector similarity via pgvector
    """
    async def _run() -> dict[str, Any]:
        from backend.shared.db import get_db_session
        from backend.shared.repository import LeadRepo
        from backend.services.dedup_service import find_duplicate, merge_leads

        async with get_db_session() as session:
            lead_repo = LeadRepo(session)
            lead = await lead_repo.get(lead_id)

            if not lead:
                return {"status": "not_found", "lead_id": lead_id}

            # Check for duplicates
            existing = await find_duplicate(lead.__dict__, session)

            if existing:
                merged = await merge_leads(existing, lead.__dict__, session)
                await session.commit()
                return {
                    "status": "merged",
                    "lead_id": lead_id,
                    "merged_into": str(merged.id),
                }

            return {"status": "unique", "lead_id": lead_id}

    return _run_async(_run())

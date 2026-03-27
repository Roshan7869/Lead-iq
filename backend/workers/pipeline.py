"""
Full Pipeline Orchestrator
Chains: collector → analyzer (Gemini/heuristic) → scoring → ranking → outreach → CRM write.

Uses high-water marks to only process new events on each run, so the pipeline
is safe to call repeatedly without reprocessing old data.
"""

from __future__ import annotations

import logging

from backend.core.config import settings
from backend.core.redis_client import redis_client
from backend.workers.collector.worker import run_collector
from backend.workers.analyzer.worker import run_analyzer
from backend.workers.scoring.worker import run_scoring
from backend.workers.ranking.worker import run_ranking
from backend.workers.outreach.worker import run_outreach
from backend.services.crm_service import write_pipeline_results

logger = logging.getLogger(__name__)


async def _get_last_stream_id(stream: str) -> str:
    """Return the ID of the most recent event in *stream*, or '0' if empty."""
    results = await redis_client.client.xrevrange(stream, "+", "-", count=1)
    if results:
        msg_id, _ = results[0]
        return msg_id
    return "0"


async def run_full_pipeline(signal_count: int = 5) -> dict:
    """
    Execute the complete lead-intelligence pipeline end-to-end.

    Captures high-water marks before each stage so that only events produced
    in *this* run are forwarded downstream.  Returns a summary dict with the
    number of events processed at each stage.
    """
    logger.info("Pipeline: starting full run (signal_count=%d)", signal_count)

    # ── Record high-water marks before each stream is written to ─────────────
    collected_hwm = await _get_last_stream_id(settings.STREAM_COLLECTED)
    analyzed_hwm = await _get_last_stream_id(settings.STREAM_ANALYZED)
    scored_hwm = await _get_last_stream_id(settings.STREAM_SCORED)
    ranked_hwm = await _get_last_stream_id(settings.STREAM_RANKED)
    outreach_hwm = await _get_last_stream_id(settings.STREAM_OUTREACH)

    # ── Stage 1: Collect demand signals ──────────────────────────────────────
    collected_ids = await run_collector(count=signal_count)
    logger.info("Pipeline [1/6] collected %d signals", len(collected_ids))

    # ── Stage 2: AI analyse (Gemini or heuristics) ───────────────────────────
    analyzed_ids = await run_analyzer(last_id=collected_hwm)
    logger.info("Pipeline [2/6] analyzed %d events", len(analyzed_ids))

    # ── Stage 3: Score leads ──────────────────────────────────────────────────
    scored_ids = await run_scoring(last_id=analyzed_hwm)
    logger.info("Pipeline [3/6] scored %d events", len(scored_ids))

    # ── Stage 4: Rank leads ───────────────────────────────────────────────────
    ranked_ids = await run_ranking(last_id=scored_hwm)
    logger.info("Pipeline [4/6] ranked %d events", len(ranked_ids))

    # ── Stage 5: Generate outreach messages ───────────────────────────────────
    outreach_ids = await run_outreach(last_id=ranked_hwm)
    logger.info("Pipeline [5/6] generated outreach for %d events", len(outreach_ids))

    # ── Stage 6: Persist to CRM store ─────────────────────────────────────────
    crm_count = await write_pipeline_results(last_id=outreach_hwm)
    logger.info("Pipeline [6/6] written %d leads to CRM", crm_count)

    return {
        "collected": len(collected_ids),
        "analyzed": len(analyzed_ids),
        "scored": len(scored_ids),
        "ranked": len(ranked_ids),
        "outreach": len(outreach_ids),
        "crm_updated": crm_count,
    }

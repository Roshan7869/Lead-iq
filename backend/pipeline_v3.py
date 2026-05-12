"""
backend/pipeline_v3.py — LeadIQ v3: Final World-Class Pipeline
Wires: 7 collectors → dedup → 12-dim score → persona recon → 4-tier LLM → signal fusion → anomalies → trends
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from backend.collectors.base import RawPost
from backend.collectors.hn import HNCollector
from backend.collectors.reddit import RedditCollector
from backend.collectors.stackoverflow import StackOverflowCollector
from backend.collectors.github_issues import GitHubIssuesCollector
from backend.collectors.scrapling_wrapper import (
    ScraplingLinkedInCollector,
    ScraplingAngelListCollector,
    ScraplingCrunchbaseCollector,
)
from backend.engine.scorer import MultiDimensionalScorer
from backend.engine.batch_scorer import BatchScorer
from backend.llm.fallback_chain import FallbackChain
from backend.enrichment.persona_recon import PersonaRecon
from backend.intelligence.signal_fusion import SignalFusionEngine
from backend.intelligence.anomaly_detector import AnomalyDetector
from backend.intelligence.trends import TrendAnalyzer

logger = logging.getLogger(__name__)


# Scoring thresholds calibrated for real-world performance
SCORE_THRESHOLDS = {
    "HOT": 70,   # Strong multi-source intent (was 85)
    "WARM": 55,  # Clear intent signal (was 65)
    "COOL": 40,  # Weak intent signal (was 50)
}


class UnifiedPipeline:
    """World-class lead pipeline: 7 collectors → dedup → 12-dim score → persona → LLM → fusion → anomalies → trends."""

    def __init__(self, use_llm: bool = True, max_concurrency: int = 20, use_graph: bool = False) -> None:
        self.scorer = MultiDimensionalScorer()
        self.batch = BatchScorer(use_llm=use_llm, max_concurrency=max_concurrency)
        self.llm = FallbackChain() if use_llm else None
        self.trend_analyzer = TrendAnalyzer()
        self.signal_fusion = SignalFusionEngine(lookback_hours=72)
        self.anomaly_detector = AnomalyDetector()
        self.persona_recon = PersonaRecon()
        self.use_llm = use_llm
        self._graph = None
        if use_graph:
            try:
                from backend.graph_db import GraphDB
                self._graph = GraphDB()
                logger.info("Neo4j graph layer enabled")
            except Exception as e:
                logger.warning("Neo4j graph init failed: %s", e)

    async def run(self) -> dict[str, Any]:
        raw_posts = await self._collect_all()
        unique = self._dedup(raw_posts)

        # Batch score all posts in parallel
        scored = await self.batch.score_batch(unique)

        # Enrich top-scoring leads with persona
        enriched = await self._enrich_top(scored, top_n=30)

        # Signal fusion + anomalies
        for lead in enriched:
            self.signal_fusion.add_signal(
                entity=lead["post"].author,
                source=lead["post"].source,
                text=f"{lead['post'].title} {lead['post'].body}",
                score=lead["score"].overall,
            )
            self.anomaly_detector.record(
                f"{lead['post'].source}_score",
                float(lead["score"].overall),
            )

        fusions = self.signal_fusion.detect_convergence()
        anomalies = self._collect_anomalies(scored)
        trend_data = self._analyze_trends(scored)

        return {
            "leads": enriched,
            "anomalies": anomalies,
            "fusions": [
                {"entities": c.entities, "sources": c.sources, "confidence": c.confidence, "fusion_score": c.fusion_score}
                for c in fusions
            ],
            "trends": trend_data,
            "stats": self._compute_stats(enriched),
        }

    async def _collect_all(self) -> list[RawPost]:
        tasks = [
            HNCollector().collect(),
            RedditCollector(limit=15).collect(),
            StackOverflowCollector(pages=1).collect(),
            GitHubIssuesCollector(per_repo=5).collect(),
            ScraplingLinkedInCollector().collect(),
            ScraplingAngelListCollector().collect(),
            ScraplingCrunchbaseCollector().collect(),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        posts: list[RawPost] = []
        for result in results:
            if isinstance(result, list):
                posts.extend(result)
            else:
                logger.debug("Collector failed: %s", result)
        return posts

    def _dedup(self, posts: list[RawPost]) -> list[RawPost]:
        seen: set[str] = set()
        unique: list[RawPost] = []
        for post in posts:
            h = post.content_hash
            if h not in seen:
                seen.add(h)
                unique.append(post)
        logger.info("Deduplicated %d posts → %d unique", len(posts), len(unique))
        return unique

    async def _enrich_top(self, scored: list[dict], top_n: int = 10) -> list[dict]:
        """Enrich top-scoring leads with persona recon (parallel, fast)."""
        scored_sorted = sorted(scored, key=lambda x: x["score"].overall, reverse=True)
        enriched = list(scored_sorted)

        # Only recon top N (save API calls, avoid rate limits)
        recon_limit = min(top_n, len(scored_sorted))

        for i in range(recon_limit):
            lead = enriched[i]
            if lead["score"].overall >= SCORE_THRESHOLDS["COOL"] and lead["post"].author and lead["post"].author not in ("unknown", "linkedin_user", "startup_founder", "funding_source"):
                try:
                    p = await asyncio.wait_for(
                        self.persona_recon.discover(lead["post"].author),
                        timeout=5.0
                    )
                    if p:
                        enriched[i]["persona"] = p
                        if p.authority_score > 60:
                            enriched[i]["score"].overall = min(enriched[i]["score"].overall + 10, 100)
                            enriched[i]["score"].confidence = enriched[i]["score"].classify()
                except TimeoutError:
                    pass
                except Exception:
                    pass

        return enriched

    def _collect_anomalies(self, leads: list[dict]) -> list[dict]:
        anomalies = []
        for lead in leads:
            a = self.anomaly_detector.record(
                f"{lead['post'].source}_score",
                float(lead["score"].overall),
            )
            if a:
                anomalies.append(a)
        return anomalies

    def _analyze_trends(self, leads: list[dict]) -> list[dict]:
        texts = [f"{lead['post'].title} {lead['post'].body}" for lead in leads[:100]]
        if texts:
            return self.trend_analyzer.extract_topics(texts)
        return []

    def _compute_stats(self, leads: list[dict]) -> dict[str, int]:
        hot = warm = cool = cold = 0
        for lead in leads:
            s = lead["score"].overall
            if s >= SCORE_THRESHOLDS["HOT"]:
                hot += 1
            elif s >= SCORE_THRESHOLDS["WARM"]:
                warm += 1
            elif s >= SCORE_THRESHOLDS["COOL"]:
                cool += 1
            else:
                cold += 1
        return {"total": len(leads), "hot": hot, "warm": warm, "cool": cool, "cold": cold}


async def run_full_pipeline() -> dict[str, Any]:
    pipeline = UnifiedPipeline(use_llm=True, max_concurrency=30)
    return await pipeline.run()
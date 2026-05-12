"""
scripts/run_scoring_test.py — Full end-to-end test of 12-dim scoring engine.
Runs real data from all collectors, scores, and prints results.
"""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.collectors.hn import HNCollector
from backend.collectors.reddit import RedditCollector
from backend.collectors.stackoverflow import StackOverflowCollector
from backend.collectors.github_issues import GitHubIssuesCollector
from backend.engine.scorer import MultiDimensionalScorer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def classify(score: int) -> str:
    if score >= 85:
        return "HOT"
    elif score >= 65:
        return "WARM"
    elif score >= 50:
        return "COOL"
    return "COLD"


async def test_all_collectors():
    """Run all collectors and score results."""
    logger.info("=== Starting world-class multi-source lead scoring test ===")
    scorer = MultiDimensionalScorer()
    all_posts = []

    logger.info("\n!== Production Multi-Dimensional Lead Score Test ===")
    scorer = MultiDimensionalScorer()
    all_posts = []

    # 1. HN Collector
    logger.info("[1/4] Running HN Collector...")
    try:
        hn_posts = await HNCollector(hits_per_query=10).collect()
        all_posts.extend([("hn", p) for p in hn_posts])
        logger.info("   Fetched %d HN posts", len(hn_posts))
    except Exception as e:
        logger.warning("   HN failed: %s", e)

    # 2. Reddit Collector
    logger.info("[2/4] Running Reddit Collector...")
    try:
        reddit_posts = await RedditCollector(limit=10, subreddits=["startups", "SaaS"]).collect()
        all_posts.extend([("reddit", p) for p in reddit_posts])
        logger.info("   └── Fetched %d Reddit posts", len(reddit_posts))
    except Exception as e:
        logger.warning("   └── Reddit failed: %s", e)

    # 3. StackOverflow Collector
    logger.info("[3/4] Running StackOverflow Collector...")
    try:
        so_posts = await StackOverflowCollector(pages=1).collect()
        all_posts.extend([("stackoverflow", p) for p in so_posts])
        logger.info("   └── Fetched %d StackOverflow posts", len(so_posts))
    except Exception as e:
        logger.warning("   └── StackOverflow failed: %s", e)

    # 4. GitHub Issues Collector
    logger.info("[4/4] Running GitHub Issues Collector...")
    try:
        gh_posts = await GitHubIssuesCollector(per_repo=5, repos=["microsoft/vscode", "facebook/react"]).collect()
        all_posts.extend([("github", p) for p in gh_posts])
        logger.info("   └── Fetched %d GitHub issues", len(gh_posts))
    except Exception as e:
        logger.warning("   └── GitHub failed: %s", e)

    # Score all
    logger.info("\n=== SCORING ===")
    scored = []
    for source, post in all_posts:
        text = f"{post.title}\n{post.body}"
        score = scorer.score(text, sources=[source], recency_days=0)
        scored.append((source, post, score))

    # Sort by score descending
    scored.sort(key=lambda x: x[2].overall, reverse=True)

    # Top 10 hot leads
    logger.info("\n--- TOP HOT/WARM LEADS ---")
    for src, post, score in scored[:10]:
        if score.confidence in ("HOT", "WARM"):
            logger.info(
                "\n[%s] %s — %d/100 [%s]\n  %s\n  Sources: %s\n  Reasons: %s",
                src.upper(),
                post.title[:80],
                score.overall,
                score.confidence,
                post.url[:100] if len(post.url) <= 100 else post.url[:97] + "...",
                ", ".join(score.sources),
                "; ".join(score.reasoning[:3]) or "N/A",
            )

    # Summary
    counts = {"HOT": 0, "WARM": 0, "COOL": 0, "COLD": 0}
    for _, _, s in scored:
        counts[s.confidence] = counts.get(s.confidence, 0) + 1
    logger.info(
        "\n🏆 Results: HOT=%d  WARM=%d  COOL=%d  COLD=%d  |  Total unique: %d",
        counts["HOT"], counts["WARM"], counts["COOL"], counts["COLD"], len(scored),
    )
    logger.info("Total anonymity: No API keys, No paid sources, No private data. 100% open-source intelligence.")


if __name__ == "__main__":
    asyncio.run(test_all_collectors())

"""
ingestion/collectors.py — Collector factory and configuration.

Provides unified access to all collectors and handles their configuration.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.collectors.base import BaseCollector


def get_collectors(
    mode: str = "b2b_sales",
    include_keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
) -> list[BaseCollector]:
    """
    Get all configured collectors for ingestion.

    Args:
        mode: Profile mode for adaptive collection (e.g., "b2b_sales", "hiring")
        include_keywords: Keywords to filter for (optional)
        exclude_keywords: Keywords to filter out (optional)

    Returns:
        List of configured collector instances
    """
    from backend.collectors.reddit import RedditCollector
    from backend.collectors.hn import HNCollector
    from backend.collectors.twitter import TwitterCollector
    from backend.collectors.rss import RSSCollector
    from backend.collectors.github import GithubCollector
    from backend.collectors.producthunt import ProductHuntCollector
    from backend.collectors.stackoverflow import StackOverflowCollector

    # Determine subreddits and queries based on mode
    if include_keywords or exclude_keywords:
        from backend.services.personalization import QueryGenerator
        qg = QueryGenerator()
        reddit_queries = qg.generate_reddit_queries(
            mode=mode,
            include_keywords=include_keywords or [],
            target_industries=[],
            hiring_roles=[],
            skills=[],
        )
        reddit_subs = qg.generate_subreddits(
            mode=mode,
            target_industries=[],
        )
    else:
        reddit_queries = None
        reddit_subs = None

    return [
        RedditCollector(
            subreddits=reddit_subs,
            search_queries=reddit_queries,
        ) if reddit_queries else RedditCollector(),
        HNCollector(),
        TwitterCollector(),
        RSSCollector(),
        GithubCollector(),
        ProductHuntCollector(),
        StackOverflowCollector(mode=mode),
        TelegramCollector(),
    ]


def get_source_names() -> list[str]:
    """Get list of all source names in ingestion order."""
    return [
        "reddit",
        "hn",
        "twitter",
        "rss",
        "github",
        "producthunt",
        "stackoverflow",
        "telegram",
    ]


def get_collector_by_source(source: str) -> type:
    """Get collector class by source name."""
    from backend.collectors.reddit import RedditCollector
    from backend.collectors.hn import HNCollector
    from backend.collectors.twitter import TwitterCollector
    from backend.collectors.rss import RSSCollector
    from backend.collectors.github import GithubCollector
    from backend.collectors.producthunt import ProductHuntCollector
    from backend.collectors.stackoverflow import StackOverflowCollector
    from backend.collectors.telegram import TelegramCollector

    mapping = {
        "reddit": RedditCollector,
        "hn": HNCollector,
        "twitter": TwitterCollector,
        "rss": RSSCollector,
        "github": GithubCollector,
        "producthunt": ProductHuntCollector,
        "stackoverflow": StackOverflowCollector,
        "telegram": TelegramCollector,
    }
    if source not in mapping:
        raise ValueError(f"Unknown source: {source}. Available: {list(mapping.keys())}")
    return mapping[source]

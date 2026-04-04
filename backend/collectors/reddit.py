"""
collectors/reddit.py — Reddit collector via PRAW (async wrapper).
Targets subreddits where buyers post pain/intent signals.

Env vars required:
  REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT

ICP subreddits (customize in SUBREDDITS list below):
  r/entrepreneur, r/startups, r/SaaS, r/smallbusiness, r/marketing,
  r/webdev, r/devops, r/aws, r/sales, r/b2bsales
"""
from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from backend.collectors.base import BaseCollector, RawPost
from backend.shared.config import settings

logger = logging.getLogger(__name__)

SUBREDDITS = [
    "entrepreneur",
    "startups",
    "SaaS",
    "smallbusiness",
    "marketing",
    "webdev",
    "devops",
    "aws",
    "sales",
    "b2bsales",
]

SEARCH_QUERIES = [
    "looking for tool",
    "recommend software",
    "need help with",
    "hunting for solution",
    "pain point",
    "anyone use",
]


class RedditCollector(BaseCollector):
    source = "reddit"

    def __init__(
        self,
        limit_per_sub: int = 25,
        subreddits: list[str] | None = None,
        search_queries: list[str] | None = None,
    ) -> None:
        self._limit   = limit_per_sub
        self._subs    = subreddits    or SUBREDDITS
        self._queries = search_queries or SEARCH_QUERIES

    async def collect(self) -> list[RawPost]:
        if not (settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET):
            logger.warning("Reddit credentials not configured — skipping RedditCollector")
            return []

        try:
            import praw  # type: ignore
        except ImportError:
            logger.error("praw not installed — run: pip install praw")
            return []

        reddit = praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT,
        )

        posts: list[RawPost] = []
        loop = asyncio.get_event_loop()

        def _fetch() -> list[RawPost]:
            collected: list[RawPost] = []
            for sub_name in self._subs:
                try:
                    sub = reddit.subreddit(sub_name)
                    for submission in sub.new(limit=self._limit):
                        collected.append(
                            RawPost(
                                source=self.source,
                                external_id=submission.id,
                                url=f"https://reddit.com{submission.permalink}",
                                title=submission.title or "",
                                body=submission.selftext or "",
                                author=str(submission.author) if submission.author else "",
                                score=submission.score,
                                collected_at=datetime.fromtimestamp(
                                    submission.created_utc, tz=UTC
                                ),
                                raw_meta={
                                    "subreddit": sub_name,
                                    "num_comments": submission.num_comments,
                                    "upvote_ratio": submission.upvote_ratio,
                                    "flair": submission.link_flair_text,
                                },
                            )
                        )
                except Exception as exc:
                    logger.warning("Error fetching r/%s: %s", sub_name, exc)
            return collected

        posts = await loop.run_in_executor(None, _fetch)
        logger.info("RedditCollector fetched %d posts", len(posts))
        return posts

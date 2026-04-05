"""
workers/github-actor/main.py — GitHub Collector Actor.

Collects GitHub user/organization profiles and enqueues to the pipeline's
Redis stream. The pipeline handles analyze → score → persist.

QUOTA: 4500 req/day (authenticated), 60 req/day (anon)
API DOCS: https://docs.github.com/en/rest
"""
from __future__ import annotations

import asyncio
import os
import structlog
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

import httpx

from backend.shared.config import settings

logger = structlog.get_logger(__name__)


GITHUB_BASE = "https://api.github.com"
QUOTA_KEY = "quota:github:{date}"
QUOTA_DAILY_MAX = 4500  # With auth token


class GitHubCollector:
    """Collects GitHub profiles and enqueues to pipeline stream."""

    def __init__(self, redis_client: Any) -> None:
        self.redis = redis_client
        self.token = os.environ.get("GITHUB_TOKEN", "")
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
        self.logger = logger

    async def _check_quota(self) -> bool:
        """
        Check + increment Redis quota counter.

        Key: quota:github:{datetime.utcnow().date()}
        Auto-expires at 86400 seconds (midnight UTC reset).

        Returns False if quota would be exceeded.
        """
        key = QUOTA_KEY.format(date=date.today().isoformat())
        try:
            current = await self.redis.get(key)
            current = int(current) if current else 0

            if current >= QUOTA_DAILY_MAX:
                self.logger.warning(
                    "github_quota_exhausted", used=current, max=QUOTA_DAILY_MAX
                )
                return False

            await self.redis.incr(key)
            await self.redis.expire(key, 86400)
            return True
        except Exception as e:
            self.logger.warning("github_quota_check_failed", error=str(e))
            return True  # Fail open if Redis unavailable

    async def fetch_profile(self, username: str) -> dict | None:
        """
        GET /users/{username}
        Returns raw GitHub API JSON or None on 404/quota_exhausted.
        """
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
                response = await client.get(f"{GITHUB_BASE}/users/{username}")

                if response.status_code == 404:
                    self.logger.info("github_user_not_found", username=username)
                    return None

                if response.status_code == 403:
                    remaining = response.headers.get("X-RateLimit-Remaining", "0")
                    reset = response.headers.get("X-RateLimit-Reset", "0")
                    if remaining == "0":
                        from datetime import datetime

                        reset_time = datetime.fromtimestamp(int(reset))
                        wait_seconds = max(1, (reset_time - datetime.now()).seconds)
                        self.logger.warning(
                            "github_rate_limited", wait_seconds=wait_seconds
                        )
                        await asyncio.sleep(wait_seconds)
                        return await self.fetch_profile(username)
                    return None

                if response.status_code == 429:
                    # Exponential backoff: 5s → 15s → 45s
                    for i, delay in enumerate([5, 15, 45]):
                        self.logger.info("github_429_backoff", attempt=i + 1, delay=delay)
                        await asyncio.sleep(delay)
                        async with httpx.AsyncClient(
                            headers=self.headers, timeout=30
                        ) as client:
                            response = await client.get(
                                f"{GITHUB_BASE}/users/{username}"
                            )
                            if response.status_code == 200:
                                return response.json()
                    return None

                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            self.logger.error("github_api_error", status=e.response.status_code)
            return None
        except Exception as e:
            self.logger.error("github_fetch_profile_failed", username=username, error=str(e))
            return None

    async def fetch_repos(self, username: str, limit: int = 10) -> list[dict]:
        """
        GET /users/{username}/repos?sort=pushed&per_page={limit}&type=owner
        Returns [] on any error (non-fatal).
        """
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
                response = await client.get(
                    f"{GITHUB_BASE}/users/{username}/repos",
                    params={
                        "sort": "pushed",
                        "per_page": limit,
                        "type": "owner",
                    },
                )

                if response.status_code == 404:
                    return []

                if response.status_code == 403:
                    # Rate limited - return empty
                    return []

                response.raise_for_status()
                return response.json()

        except Exception as e:
            self.logger.warning(
                "github_fetch_repos_failed", username=username, error=str(e)
            )
            return []

    def aggregate_tech_stack(self, repos: list[dict]) -> list[str]:
        """
        ZERO TOKENS — pure Python aggregation.

        1. Counter(r["language"] for r in repos if r.get("language"))
        2. repo topics: r.get("topics", []) accumulated
        3. Merge, deduplicate, sort by frequency
        4. Exclude: ["jupyter-notebook", "makefile", "dockerfile", "shell"]
        5. Return top 7
        """
        language_counter = Counter()
        all_topics = []

        EXCLUDE_LANGUAGES = [
            "jupyter-notebook",
            "makefile",
            "dockerfile",
            "shell",
            "shellscript",
        ]

        for repo in repos:
            language = repo.get("language")
            if language and language.lower() not in EXCLUDE_LANGUAGES:
                language_counter[language] += 1
            all_topics.extend(repo.get("topics", []))

        # Build tech stack from languages (sorted by freq)
        tech_stack = [
            lang for lang, _ in language_counter.most_common(7)
            if lang.lower() not in EXCLUDE_LANGUAGES
        ]

        # Add unique topics (sorted by freq)
        topic_counter = Counter(all_topics)
        for topic, _ in topic_counter.most_common(7):
            if topic not in tech_stack and topic.lower() not in EXCLUDE_LANGUAGES:
                tech_stack.append(topic)

        return tech_stack[:7]

    def to_pipeline_message(
        self,
        profile: dict,
        repos: list[dict],
        tech_stack: list[str],
    ) -> dict:
        """
        Formats data to match the pipeline stream schema.

        The text field (passed to GeminiAnalyzer.analyze()) contains structured
        markdown profile data that will be analyzed by the pipeline.
        """
        # Build text content for Gemini
        name = profile.get("name", profile.get("login", ""))
        company = profile.get("company", "")
        location = profile.get("location", "")
        bio = profile.get("bio", "")
        email = profile.get("email") or "Not disclosed"
        website = profile.get("blog", "")
        public_repos = profile.get("public_repos", 0)
        followers = profile.get("followers", 0)
        html_url = profile.get("html_url", "")

        text_content = f"""# {name}
**Company:** {company}
**Location:** {location}
**Bio:** {bio}
**Email:** {email}
**Website:** {website}
**Tech Stack:** {', '.join(tech_stack) if tech_stack else 'None listed'}
**Public Repos:** {public_repos}
**Followers:** {followers}
**GitHub:** {html_url}
"""

        # Build the message matching the pipeline stream schema
        message = {
            "id": f"github-{profile.get('login', 'unknown')}-{profile.get('id', '')}",
            "source": "github_profile",
            "external_id": str(profile.get("id", "")),
            "url": html_url,
            "title": f"GitHub Profile: {name}",
            "body": text_content,
            "author": profile.get("login", ""),
            "score": public_repos,
            "content_hash": str(profile.get("id", "")),
            "raw_meta": {
                "github_login": profile.get("login"),
                "github_id": profile.get("id"),
                "created_at": profile.get("created_at"),
                "updated_at": profile.get("updated_at"),
                "followers": followers,
                "following": profile.get("following", 0),
            },
            "collected_at": datetime.utcnow().isoformat(),
        }

        return message

    async def collect_profile(
        self, username: str, pipeline_stream: str
    ) -> dict:
        """
        Full collection pipeline for one username.
        """
        # 1. Check quota
        if not await self._check_quota():
            return {"status": "quota_exhausted", "username": username}

        # 2. Fetch profile
        profile = await self.fetch_profile(username)
        if profile is None:
            return {"status": "not_found", "username": username}

        # 3. Fetch repos
        repos = await self.fetch_repos(username)

        # 4. Aggregate tech stack
        tech_stack = self.aggregate_tech_stack(repos)

        # 5. Create pipeline message
        message = self.to_pipeline_message(profile, repos, tech_stack)

        # 6. Publish to pipeline stream
        entry_id = await self.redis.xadd(pipeline_stream, message)

        self.logger.info(
            "github_profile_collected",
            username=username,
            entry_id=entry_id,
            stream=pipeline_stream,
        )

        return {
            "status": "queued",
            "username": username,
            "entry_id": entry_id,
            "tech_stack": tech_stack,
        }

    async def search_india_founders(
        self, tech: str, location: str = "India", pages: int = 2
    ) -> list[str]:
        """
        GET /search/users?q={tech}+location:{location}&per_page=30&page={p}
        Returns list of usernames only.
        """
        usernames = []

        for page in range(1, pages + 1):
            # Check quota per page (search API costs quota)
            if not await self._check_quota():
                self.logger.info(
                    "github_search_quota_exhausted", tech=tech, page=page
                )
                break

            try:
                async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
                    query = f"{tech}+location:{location}"
                    response = await client.get(
                        f"{GITHUB_BASE}/search/users",
                        params={
                            "q": query,
                            "per_page": 30,
                            "page": page,
                        },
                    )

                    if response.status_code == 422:
                        # Validation failed query - return empty
                        return []

                    if response.status_code == 403:
                        # Rate limited
                        break

                    response.raise_for_status()
                    data = response.json()

                    for item in data.get("items", []):
                        login = item.get("login")
                        if login:
                            usernames.append(login)

            except Exception as e:
                self.logger.warning(
                    "github_search_failed", tech=tech, page=page, error=str(e)
                )

        return usernames

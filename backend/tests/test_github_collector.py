"""
tests/test_github_collector.py — Tests for GitHub collector actor.
"""
from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from workers.github_actor.main import GitHubCollector


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=None)
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=None)
    redis.xadd = AsyncMock(return_value="entry-id-123")
    return redis


@pytest.fixture
def github_collector(mock_redis):
    """Create a GitHubCollector instance with mocked dependencies."""
    return GitHubCollector(mock_redis)


@pytest.mark.asyncio
async def test_check_quota_blocks_at_limit(github_collector: GitHubCollector):
    """Test _check_quota() returns False when quota is exhausted."""
    # Mock Redis to return quota at limit
    github_collector.redis.get = AsyncMock(return_value="4500")

    result = await github_collector._check_quota()

    assert result is False
    github_collector.redis.incr.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_profile_404_returns_none(github_collector: GitHubCollector):
    """Test fetch_profile() returns None on 404."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404")
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        result = await github_collector.fetch_profile("nonexistent")

        assert result is None


@pytest.mark.asyncio
async def test_aggregate_tech_stack_sorted_by_frequency(github_collector: GitHubCollector):
    """Test aggregate_tech_stack() sorts by frequency."""
    repos = [
        {"language": "Python"},
        {"language": "TypeScript"},
        {"language": "Python"},
        {"language": "Go"},
        {"language": "Python"},
        {"language": "TypeScript"},
    ]

    result = github_collector.aggregate_tech_stack(repos)

    assert result == ["Python", "TypeScript", "Go"]


@pytest.mark.asyncio
async def test_to_pipeline_message_has_required_keys(github_collector: GitHubCollector):
    """Test to_pipeline_message() produces correct schema."""
    profile = {
        "login": "testuser",
        "id": 12345,
        "name": "Test User",
        "company": "Test Inc",
        "location": "Remote",
        "bio": "Software Engineer",
        "email": "test@example.com",
        "blog": "https://example.com",
        "public_repos": 10,
        "followers": 100,
        "html_url": "https://github.com/testuser",
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    repos = [{"language": "Python"}]
    tech_stack = ["Python", "JavaScript"]

    message = github_collector.to_pipeline_message(profile, repos, tech_stack)

    assert "id" in message
    assert "source" in message
    assert message["source"] == "github_profile"
    assert "external_id" in message
    assert "url" in message
    assert "title" in message
    assert "body" in message
    assert "author" in message
    assert "score" in message
    assert "content_hash" in message
    assert "raw_meta" in message
    assert "collected_at" in message


@pytest.mark.asyncio
async def test_collect_profile_writes_to_stream(github_collector: GitHubCollector):
    """Test collect_profile() writes to Redis stream."""
    profile = {
        "login": "testuser",
        "id": 12345,
        "name": "Test User",
        "company": "Test Inc",
        "location": "Remote",
        "bio": "Software Engineer",
        "email": "test@example.com",
        "blog": "https://example.com",
        "public_repos": 10,
        "followers": 100,
        "html_url": "https://github.com/testuser",
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }

    # Mock all the dependencies
    github_collector.redis.get = AsyncMock(return_value=None)
    github_collector.redis.set = AsyncMock(return_value=None)
    github_collector.redis.incr = AsyncMock(return_value=1)
    github_collector.redis.expire = AsyncMock(return_value=None)
    github_collector.redis.xadd = AsyncMock(return_value="entry-id-123")
    github_collector.fetch_profile = AsyncMock(return_value=profile)
    github_collector.fetch_repos = AsyncMock(return_value=[])
    github_collector.aggregate_tech_stack = MagicMock(return_value=["Python"])

    result = await github_collector.collect_profile("testuser", "lead:collected")

    assert result["status"] == "queued"
    assert result["username"] == "testuser"
    assert result["entry_id"] == "entry-id-123"
    github_collector.redis.xadd.assert_called_once()


@pytest.mark.asyncio
async def test_collect_profile_quota_exhausted_early_return(github_collector: GitHubCollector):
    """Test collect_profile() returns early when quota exhausted."""
    github_collector.redis.get = AsyncMock(return_value="4500")

    result = await github_collector.collect_profile("testuser", "lead:collected")

    assert result["status"] == "quota_exhausted"
    github_collector.redis.xadd.assert_not_called()
    github_collector.fetch_profile.assert_not_called()


@pytest.mark.asyncio
async def test_search_india_founders_returns_usernames(github_collector: GitHubCollector):
    """Test search_india_founders() returns usernames from search."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value={
            "items": [
                {"login": "user1"},
                {"login": "user2"},
            ]
        })
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        github_collector.redis.get = AsyncMock(return_value=None)
        github_collector.redis.incr = AsyncMock(return_value=1)

        results = await github_collector.search_india_founders("python", "India", pages=1)

        assert results == ["user1", "user2"]


@pytest.mark.asyncio
async def test_fetch_profile_rate_limit_exponential_backoff(github_collector: GitHubCollector):
    """Test fetch_profile() handles 429 with exponential backoff."""
    with patch("httpx.AsyncClient") as mock_client:
        with patch("asyncio.sleep") as mock_sleep:
            # First call returns 429, second returns success
            responses = [
                MagicMock(status_code=429, headers={}),
                MagicMock(status_code=200, json=lambda: {"login": "testuser"}),
            ]

            async def get_response(*args, **kwargs):
                return responses.pop(0)

            mock_client.return_value.__aenter__.return_value.get = get_response

            result = await github_collector.fetch_profile("testuser")

            assert result is not None
            assert result["login"] == "testuser"


@pytest.mark.asyncio
async def test_fetch_repos_error_returns_empty(github_collector: GitHubCollector):
    """Test fetch_repos() returns [] on any error."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        result = await github_collector.fetch_repos("testuser")

        assert result == []


@pytest.mark.asyncio
async def test_aggregate_tech_stack_excludes_special_files(github_collector: GitHubCollector):
    """Test aggregate_tech_stack() excludes special file types."""
    repos = [
        {"language": "Python"},
        {"language": "Jupyter Notebook"},
        {"language": "Makefile"},
        {"language": "Dockerfile"},
        {"language": "Shell"},
        {"language": "Python"},
    ]

    result = github_collector.aggregate_tech_stack(repos)

    assert "Python" in result
    assert "Jupyter Notebook" not in result
    assert "Makefile" not in result
    assert "Dockerfile" not in result
    assert "Shell" not in result

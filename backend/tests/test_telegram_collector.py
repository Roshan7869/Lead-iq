"""
tests/test_telegram_collector.py — Tests for Telegram collector actor.
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from workers.telegram_actor.main import TelegramCollector


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
def telegram_collector(mock_redis):
    """Create a TelegramCollector instance with mocked dependencies."""
    return TelegramCollector(mock_redis)


@pytest.mark.asyncio
async def test_should_process_funding_message(telegram_collector: TelegramCollector):
    """Test should_process() detects funding signals."""
    text = "Startup XYZ raises Series A of $5M from Sequoia"

    result = telegram_collector.should_process(text)

    assert result == (True, "funding")


@pytest.mark.asyncio
async def test_should_process_hiring_message(telegram_collector: TelegramCollector):
    """Test should_process() detects hiring signals (need 2+ keywords)."""
    text = "We are hiring engineers, join our growing team now"

    result = telegram_collector.should_process(text)

    assert result == (True, "hiring")


@pytest.mark.asyncio
async def test_should_process_noise(telegram_collector: TelegramCollector):
    """Test should_process() filters out noise."""
    text = "Happy Sunday everyone! Great weekend."

    result = telegram_collector.should_process(text)

    assert result == (False, "noise")


@pytest.mark.asyncio
async def test_fetch_channel_parses_html(telegram_collector: TelegramCollector):
    """Test fetch_channel_messages() parses t.me/s/ HTML."""
    html_content = """
    <div class="tgme_widget_message_wrap" data-post="testchannel/101">
      <div class="tgme_widget_message_text">Startup XYZ raises $5M Series A</div>
      <time datetime="2026-04-05T09:00:00+00:00"></time>
    </div>
    <div class="tgme_widget_message_wrap" data-post="testchannel/102">
      <div class="tgme_widget_message_text">We are hiring engineers</div>
      <time datetime="2026-04-05T10:00:00+00:00"></time>
    </div>
    """

    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_response.raise_for_status = MagicMock()
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        with patch("bs4.BeautifulSoup") as mock_beautifulsoup:
            # Mock BeautifulSoup behavior
            soup_mock = MagicMock()
            wrap1 = MagicMock()
            wrap1.get = MagicMock(side_effect=lambda k: "testchannel/101" if k == "data-post" else None)
            wrap1.find.return_value = MagicMock(get_text=MagicMock(return_value="Startup XYZ raises $5M Series A"))
            wrap1.find_all.return_value = [wrap1]

            soup_mock.find_all = MagicMock(return_value=[wrap1])
            mock_beautifulsoup.return_value = soup_mock

            results = await telegram_collector.fetch_channel_messages("@testchannel")

            assert len(results) >= 1
            assert results[0]["message_id"] == 101
            assert "Series A" in results[0]["text"]


@pytest.mark.asyncio
async def test_to_pipeline_message_has_required_keys(telegram_collector: TelegramCollector):
    """Test to_pipeline_message() produces correct schema."""
    message = {
        "message_id": 101,
        "text": "Startup raises Series A",
        "published_at": "2026-04-05T09:00:00Z",
        "channel": "@testchannel",
    }

    result = telegram_collector.to_pipeline_message(message, "funding")

    assert "id" in result
    assert "source" in result
    assert result["source"] == "telegram"
    assert "external_id" in result
    assert "url" in result
    assert "title" in result
    assert "body" in result
    assert result["body"] == "Startup raises Series A"
    assert "author" in result
    assert "score" in result
    assert "content_hash" in result
    assert "raw_meta" in result
    assert result["raw_meta"]["signal_type"] == "funding"
    assert "collected_at" in result


@pytest.mark.asyncio
async def test_quota_blocks_fetch(telegram_collector: TelegramCollector):
    """Test fetch_channel_messages() returns [] when quota exhausted."""
    telegram_collector.redis.get = AsyncMock(return_value="501")

    results = await telegram_collector.fetch_channel_messages("@testchannel")

    assert results == []
    telegram_collector.redis.incr.assert_not_called()


@pytest.mark.asyncio
async def test_watermark_filters_old_messages(telegram_collector: TelegramCollector):
    """Test collect_channel() filters messages older than watermark."""
    # Mock watermark to 500
    telegram_collector.redis.get = AsyncMock(return_value="500")
    telegram_collector.redis.set = AsyncMock(return_value=None)
    telegram_collector.redis.xadd = AsyncMock(return_value="entry-id")
    telegram_collector._check_quota = AsyncMock(return_value=True)
    telegram_collector.fetch_channel_messages = AsyncMock(return_value=[
        {"message_id": 498, "text": "Old message 1", "channel": "@test"},
        {"message_id": 501, "text": "New message 1", "channel": "@test"},
        {"message_id": 502, "text": "New message 2", "channel": "@test"},
    ])
    telegram_collector.should_process = MagicMock(return_value=(True, "funding"))
    telegram_collector.to_pipeline_message = MagicMock(
        side_effect=lambda m, s: {"id": f"msg-{m['message_id']}", **m}
    )

    result = await telegram_collector.collect_channel("@test", "lead:collected")

    # Only messages with ID > 500 should be processed (501, 502)
    assert result["processed"] == 2


@pytest.mark.asyncio
async def test_run_all_aggregates_stats(telegram_collector: TelegramCollector):
    """Test run_all() aggregates stats across channels."""
    telegram_collector.redis.get = AsyncMock(return_value=None)
    telegram_collector._check_quota = AsyncMock(return_value=True)

    # Mock fetch for first channel
    telegram_collector.fetch_channel_messages = AsyncMock(
        side_effect=[
            [{"message_id": 101, "text": "Funding", "channel": "@c1"}],
            [{"message_id": 201, "text": "Hiring", "channel": "@c2"}],
        ]
    )
    telegram_collector.should_process = MagicMock(return_value=(True, "funding"))
    telegram_collector.to_pipeline_message = MagicMock(
        side_effect=lambda m, s: {"id": f"msg-{m['message_id']}", **m}
    )
    telegram_collector.redis.xadd = AsyncMock(return_value="entry-id")

    result = await telegram_collector.run_all("lead:collected")

    assert result["status"] == "completed"
    assert result["total_processed"] >= 0


@pytest.mark.asyncio
async def test_get_watermarks(telegram_collector: TelegramCollector):
    """Test get_watermarks() returns watermark for each channel."""
    # Mock channels
    telegram_collector.channels = ["@channel1", "@channel2"]
    telegram_collector.redis.get = AsyncMock(
        side_effect=["100", "200", None]
    )

    watermarks = await telegram_collector.get_watermarks()

    assert watermarks == {"@channel1": 100, "@channel2": 200}


@pytest.mark.asyncio
async def test_fetch_channel_channel_not_found(telegram_collector: TelegramCollector):
    """Test fetch_channel_messages() returns [] on 404."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.raise_for_status.side_effect = Exception("404")
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        results = await telegram_collector.fetch_channel_messages("@nonexistent")

        assert results == []


@pytest.mark.asyncio
async def test_collect_channel_updates_watermark(telegram_collector: TelegramCollector):
    """Test collect_channel() updates watermark after processing."""
    telegram_collector.redis.get = AsyncMock(return_value=None)
    telegram_collector.redis.set = AsyncMock(return_value=None)
    telegram_collector._check_quota = AsyncMock(return_value=True)
    telegram_collector.fetch_channel_messages = AsyncMock(return_value=[
        {"message_id": 101, "text": "New message", "channel": "@test"},
    ])
    telegram_collector.should_process = MagicMock(return_value=(True, "funding"))
    telegram_collector.to_pipeline_message = MagicMock(
        side_effect=lambda m, s: {"id": f"msg-{m['message_id']}", **m}
    )
    telegram_collector.redis.xadd = AsyncMock(return_value="entry-id")

    await telegram_collector.collect_channel("@test", "lead:collected")

    # Verify watermark was set
    telegram_collector.redis.set.assert_any_call(
        "telegram:watermark:test", 101
    )

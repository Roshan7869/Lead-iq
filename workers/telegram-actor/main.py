"""
workers/telegram-actor/main.py — Telegram Collector Actor.

Scrapes t.me/s/{channel} for funding/hiring signals and enqueues to
the pipeline's Redis stream. Uses public preview HTML (no bot token required).

QUOTA: 500 requests/day (t.me/s/ scraping)
"""
from __future__ import annotations

import asyncio
import os
import re
import structlog
from datetime import date, datetime
from typing import Any

import httpx
from bs4 import BeautifulSoup

from backend.shared.config import settings

logger = structlog.get_logger(__name__)


# Funding keywords (Tier 1 - strong signals)
FUNDING_KEYWORDS_T1 = [
    "raises", "raised", "funding", "series a", "series b", "series c",
    "seed round", "pre-seed", "crore", "million", "billion",
    "backed by", "investment", "valuation", "unicorn", "acqui",
]

# Hiring keywords (Tier 2 - need 2+ matches)
FUNDING_KEYWORDS_T2 = [
    "hiring", "we're growing", "join our team", "open position",
    "we're looking for", "new opening", "we are hiring", "job opening",
]


class TelegramCollector:
    """Scrapes Telegram channels for funding/hiring signals."""

    def __init__(self, redis_client: Any) -> None:
        self.redis = redis_client
        self.channels = os.environ.get(
            "TELEGRAM_WATCHED_CHANNELS",
            "@inc42,@startupsindia,@yourstory",
        ).split(",")
        self.quota_key = "quota:telegram:{date}"
        self.quota_max = 500  # per day (t.me/s/ requests)
        self.watermark_key = "telegram:watermark:{channel}"
        self.logger = logger

    async def _check_quota(self) -> bool:
        """
        Check + increment Redis quota counter.

        Key: quota:telegram:{datetime.utcnow().date()}
        Auto-expires at 86400 seconds (midnight UTC reset).

        Returns False if quota would be exceeded.
        """
        key = self.quota_key.format(date=date.today().isoformat())
        try:
            current = await self.redis.get(key)
            current = int(current) if current else 0

            if current >= self.quota_max:
                self.logger.warning(
                    "telegram_quota_exhausted", used=current, max=self.quota_max
                )
                return False

            await self.redis.incr(key)
            await self.redis.expire(key, 86400)
            return True
        except Exception as e:
            self.logger.warning("telegram_quota_check_failed", error=str(e))
            return True  # Fail open if Redis unavailable

    async def fetch_channel_messages(
        self, channel: str, limit: int = 50
    ) -> list[dict]:
        """
        GET https://t.me/s/{channel.lstrip('@')}
        Parse HTML with BeautifulSoup.

        Returns list of:
          {"message_id": int, "text": str, "published_at": str, "channel": str}
        """
        channel_clean = channel.lstrip("@")
        url = f"https://t.me/s/{channel_clean}"

        # Check quota
        if not await self._check_quota():
            self.logger.info("telegram_quota_exhausted", channel=channel)
            return []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url)

                if response.status_code == 404:
                    self.logger.error("telegram_channel_not_found", channel=channel)
                    return []

                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # Find all message wrappers
                messages = []
                message_wraps = soup.find_all(
                    "div", class_="tgme_widget_message_wrap"
                )

                for wrap in message_wraps[:limit]:
                    # Extract message ID from data-post attribute
                    data_post = wrap.get("data-post", "")
                    message_id = 0
                    if data_post:
                        parts = data_post.split("/")
                        if len(parts) >= 2:
                            try:
                                message_id = int(parts[-1])
                            except ValueError:
                                pass

                    # Extract text
                    text_div = wrap.find("div", class_="tgme_widget_message_text")
                    text = text_div.get_text(strip=True) if text_div else ""

                    # Extract time
                    time_tag = wrap.find("time")
                    published_at = ""
                    if time_tag and time_tag.get("datetime"):
                        published_at = time_tag["datetime"]

                    if text:
                        messages.append({
                            "message_id": message_id,
                            "text": text,
                            "published_at": published_at,
                            "channel": channel,
                        })

                self.logger.info(
                    "telegram_messages_fetched",
                    channel=channel,
                    count=len(messages),
                )
                return messages

        except Exception as e:
            self.logger.warning(
                "telegram_fetch_failed", channel=channel, error=str(e)
            )
            return []

    def should_process(self, text: str) -> tuple[bool, str]:
        """
        Pre-filter - FREE, no API call.

        Returns (True, "funding") or (True, "hiring") or (False, "noise")
        """
        text_lower = text.lower()

        # Count tier 1 hits
        t1_hits = sum(
            1 for k in FUNDING_KEYWORDS_T1 if k in text_lower
        )

        # Count tier 2 hits
        t2_hits = sum(
            1 for k in FUNDING_KEYWORDS_T2 if k in text_lower
        )

        if t1_hits >= 1:
            return (True, "funding")

        if t2_hits >= 2:
            return (True, "hiring")

        return (False, "noise")

    def to_pipeline_message(
        self, message: dict, signal_type: str
    ) -> dict:
        """
        Map Telegram message to pipeline stream schema.

        text   = message["text"]  ← this goes to GeminiAnalyzer.analyze()
        source = "telegram"
        author = message["channel"]
        """
        return {
            "id": f"telegram-{message['channel'].lstrip('@')}-{message['message_id']}",
            "source": "telegram",
            "external_id": str(message["message_id"]),
            "url": f"https://t.me/{message['channel'].lstrip('@')}/{message['message_id']}",
            "title": f"Telegram: {message['channel']}",
            "body": message["text"],
            "author": message["channel"],
            "score": 1,  # Telegram message count proxy
            "content_hash": f"tg-{message['message_id']}",
            "raw_meta": {
                "signal_type": signal_type,
                "published_at": message.get("published_at"),
                "channel": message["channel"],
            },
            "collected_at": datetime.utcnow().isoformat(),
        }

    async def collect_channel(
        self, channel: str, pipeline_stream: str
    ) -> dict:
        """
        Full collection pipeline for one channel.

        1. Get watermark: last_id = Redis.get(...) or 0
        2. fetch_channel_messages(channel) → messages
        3. Filter: messages where message_id > last_id (new only)
        4. For each new message: should_process → to_pipeline_message → xadd
        5. Update watermark
        6. Return stats dict
        """
        # 1. Get watermark
        watermark_key = self.watermark_key.format(channel=channel.lstrip("@"))
        try:
            last_id_raw = await self.redis.get(watermark_key)
            last_id = int(last_id_raw) if last_id_raw else 0
        except Exception:
            last_id = 0

        # 2. Fetch messages
        messages = await self.fetch_channel_messages(channel)

        # 3-4. Process new messages
        processed = 0
        queued = 0
        filtered = 0

        for msg in messages:
            msg_id = msg.get("message_id", 0)

            # Filter by watermark
            if msg_id <= last_id:
                filtered += 1
                continue

            # Pre-filter
            should_process, signal_type = self.should_process(msg.get("text", ""))
            if not should_process:
                filtered += 1
                continue

            # Convert to pipeline message and enqueue
            pipeline_msg = self.to_pipeline_message(msg, signal_type)
            try:
                entry_id = await self.redis.xadd(pipeline_stream, pipeline_msg)
                processed += 1
                queued += 1
                self.logger.info(
                    "telegram_message_queued",
                    channel=channel,
                    message_id=msg_id,
                    signal_type=signal_type,
                    entry_id=entry_id,
                )
            except Exception as e:
                self.logger.error(
                    "telegram_queue_failed",
                    channel=channel,
                    message_id=msg_id,
                    error=str(e),
                )

        # 5. Update watermark (max message_id processed)
        if processed > 0:
            new_max = max(msg.get("message_id", 0) for msg in messages if msg.get("message_id", 0) > last_id)
            await self.redis.set(watermark_key, new_max)
            await self.redis.expire(watermark_key, 86400 * 7)  # 7 days

        return {
            "channel": channel,
            "messages_fetched": len(messages),
            "processed": processed,
            "queued": queued,
            "filtered": filtered,
            "last_watermark": last_id,
        }

    async def run_all(self, pipeline_stream: str) -> dict:
        """
        Called by Celery beat every 2 hours.
        Runs collect_channel() for each channel in self.channels.
        """
        results = []
        total_processed = 0
        total_queued = 0

        for channel in self.channels:
            result = await self.collect_channel(channel, pipeline_stream)
            results.append(result)
            total_processed += result.get("processed", 0)
            total_queued += result.get("queued", 0)

        return {
            "status": "completed",
            "channels": results,
            "total_processed": total_processed,
            "total_queued": total_queued,
        }

    async def get_watermarks(self) -> dict[str, int]:
        """Get all current watermarks for watched channels."""
        watermarks = {}
        for channel in self.channels:
            key = self.watermark_key.format(channel=channel.lstrip("@"))
            try:
                value = await self.redis.get(key)
                watermarks[channel] = int(value) if value else 0
            except Exception:
                watermarks[channel] = 0
        return watermarks

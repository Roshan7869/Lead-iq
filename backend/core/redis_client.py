"""
Redis client — Core Infrastructure (Phase 1)
Event bus: lead:collected, lead:analyzed, lead:scored, lead:ranked, lead:outreach, lead:crm_update
"""

import json
from typing import Any

import redis.asyncio as aioredis

from backend.core.config import settings


class RedisClient:
    def __init__(self):
        self._client: aioredis.Redis | None = None

    async def connect(self) -> None:
        self._client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    async def disconnect(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> aioredis.Redis:
        if not self._client:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client

    # ── Event Stream Helpers ──────────────────────────────────────────────────

    async publish(self, stream: str, data: dict[str, Any]) -> str:
        """Publish an event to a Redis stream (XADD). Returns the event ID."""
        payload: dict[str, str] = {}
        for k, v in data.items():
            if isinstance(v, str):
                payload[k] = v
            else:
                try:
                    payload[k] = json.dumps(v)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Field '{k}' in stream '{stream}' is not JSON-serialisable: {exc!r}"
                    ) from exc
        return await self.client.xadd(stream, payload)

    async def consume(
        self,
        stream: str,
        last_id: str = "0",
        count: int = 100,
    ) -> list[tuple[str, dict]]:
        """Read events from a Redis stream (XREAD). Returns list of (id, data) tuples."""
        results = await self.client.xread({stream: last_id}, count=count)
        if not results:
            return []
        _, messages = results[0]
        return [(msg_id, {k: _try_json(v) for k, v in fields.items()}) for msg_id, fields in messages]

    async def get_stream_length(self, stream: str) -> int:
        return await self.client.xlen(stream)


def _try_json(value: str) -> Any:
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


redis_client = RedisClient()

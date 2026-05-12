"""
url_scheduler.py — Priority queue with URL deduplication for crawl scheduling.

Directly merged from Scrapling (scrapling/spiders/scheduler.py).
Used by the scrapling adapter to manage crawl queues with checkpoint support.
"""
from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass, field
from itertools import count
from typing import Any


@dataclass
class CrawlRequest:
    url: str
    priority: int = 0
    callback: str = "parse"
    dont_filter: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def fingerprint(self) -> bytes:
        canonical = self.url.strip().lower().encode("utf-8")
        return hashlib.sha256(canonical).digest()


class Scheduler:
    def __init__(self, include_kwargs: bool = False, keep_fragments: bool = False):
        self._queue: asyncio.PriorityQueue[tuple[int, int, CrawlRequest]] = asyncio.PriorityQueue()
        self._seen: set[bytes] = set()
        self._counter = count()
        self._pending: dict[int, tuple[int, int, CrawlRequest]] = {}
        self._include_kwargs = include_kwargs
        self._keep_fragments = keep_fragments

    async def enqueue(self, request: CrawlRequest) -> bool:
        fp = request.fingerprint()
        if not request.dont_filter and fp in self._seen:
            return False
        self._seen.add(fp)
        counter = next(self._counter)
        item = (-request.priority, counter, request)
        self._pending[counter] = item
        await self._queue.put(item)
        return True

    async def dequeue(self) -> CrawlRequest:
        _, counter, request = await self._queue.get()
        self._pending.pop(counter, None)
        return request

    def __len__(self) -> int:
        return self._queue.qsize()

    @property
    def is_empty(self) -> bool:
        return self._queue.empty()

    def snapshot(self) -> tuple[list[CrawlRequest], set[bytes]]:
        sorted_items = sorted(self._pending.values(), key=lambda x: (x[0], x[1]))
        requests = [item[2] for item in sorted_items]
        return requests, self._seen.copy()

    def restore(self, requests: list[CrawlRequest], seen: set[bytes]) -> None:
        self._seen = seen.copy()
        for request in requests:
            counter = next(self._counter)
            item = (-request.priority, counter, request)
            self._pending[counter] = item
            self._queue.put_nowait(item)

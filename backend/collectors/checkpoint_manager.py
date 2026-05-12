"""
checkpoint_manager.py — Pause/resume long crawls via disk checkpoints.

Directly merged from Scrapling (scrapling/spiders/checkpoint.py).
Serializes scheduler state so crawls survive process restarts.
"""
from __future__ import annotations

import pickle
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from backend.collectors.url_scheduler import CrawlRequest

logger = structlog.get_logger(__name__)


@dataclass
class CheckpointData:
    requests: list[CrawlRequest] = field(default_factory=list)
    seen: set[bytes] = field(default_factory=set)


class CheckpointManager:
    CHECKPOINT_FILE = "checkpoint.pkl"

    def __init__(self, crawldir: str | Path, interval: float = 300.0):
        self.crawldir = Path(crawldir)
        self._checkpoint_path = self.crawldir / self.CHECKPOINT_FILE
        self.interval = interval
        if interval < 0:
            raise ValueError("Checkpoints interval must be >= 0")

    def has_checkpoint(self) -> bool:
        return self._checkpoint_path.exists()

    def save(self, data: CheckpointData) -> None:
        self.crawldir.mkdir(parents=True, exist_ok=True)
        temp_path = self._checkpoint_path.with_suffix(".tmp")
        try:
            with open(temp_path, "wb") as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            temp_path.rename(self._checkpoint_path)
            logger.info("checkpoint_saved", requests=len(data.requests), seen=len(data.seen))
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

    def load(self) -> CheckpointData | None:
        if not self.has_checkpoint():
            return None
        try:
            with open(self._checkpoint_path, "rb") as f:
                data: CheckpointData = pickle.load(f)
            logger.info("checkpoint_loaded", requests=len(data.requests), seen=len(data.seen))
            return data
        except Exception as e:
            logger.warning("checkpoint_load_failed", error=str(e))
            return None

    def cleanup(self) -> None:
        try:
            if self._checkpoint_path.exists():
                self._checkpoint_path.unlink()
        except Exception as e:
            logger.warning("checkpoint_cleanup_failed", error=str(e))

"""
retry_handler.py — Intelligent retry logic with exponential backoff and jitter.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Coroutine
from functools import wraps
from typing import Any, Callable, TypeVar

import structlog

logger = structlog.get_logger()

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behaviour."""

    max_attempts: int = 5
    base_delay: float = 2.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple = (
        asyncio.TimeoutError,
        ConnectionError,
        ConnectionRefusedError,
        ConnectionResetError,
        ConnectionAbortedError,
    )

    def __init__(
        self,
        max_attempts: int = 5,
        base_delay: float = 2.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: tuple | None = None,
    ) -> None:
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        if retryable_exceptions is not None:
            self.retryable_exceptions = retryable_exceptions


class RetryHandler:
    """Handle retries with exponential backoff and jitter."""

    def __init__(self, config: RetryConfig | None = None) -> None:
        self.config = config or RetryConfig()

    async def execute(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute *func* with retry logic."""
        last_exception: Exception | None = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                result = await func(*args, **kwargs)
                if attempt > 1:
                    logger.info(
                        "retry_succeeded",
                        attempt=attempt,
                        func=func.__name__,
                    )
                return result
            except Exception as exc:
                last_exception = exc
                if not self._is_retryable(exc):
                    raise

                if attempt == self.config.max_attempts:
                    logger.error(
                        "max_retries_exceeded",
                        func=func.__name__,
                        error=str(exc),
                        attempts=attempt,
                    )
                    raise

                delay = self._calculate_delay(attempt)
                logger.warning(
                    "retry_attempt",
                    func=func.__name__,
                    attempt=attempt,
                    delay=delay,
                    error=str(exc),
                )
                await asyncio.sleep(delay)

        raise RuntimeError("unreachable")  # pragma: no cover

    def _is_retryable(self, exception: Exception) -> bool:
        return isinstance(exception, self.config.retryable_exceptions)

    def _calculate_delay(self, attempt: int) -> float:
        delay = self.config.base_delay * (
            self.config.exponential_base ** (attempt - 1)
        )
        delay = min(delay, self.config.max_delay)
        if self.config.jitter:
            jitter = delay * 0.3 * random.uniform(-1, 1)
            delay = max(0.5, delay + jitter)
        return delay


def with_retry(config: RetryConfig | None = None) -> Callable:
    """Decorator that wraps an async function with retry logic."""
    handler = RetryHandler(config)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await handler.execute(func, *args, **kwargs)

        return wrapper

    return decorator

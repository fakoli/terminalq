"""Token bucket rate limiter for API providers."""
import asyncio
import time


class RateLimiter:
    """Async token bucket rate limiter.

    Allows burst up to bucket size, then throttles to calls_per_minute.
    """

    def __init__(self, calls_per_minute: int = 60):
        self._rate = calls_per_minute / 60.0  # tokens per second
        self._max_tokens = calls_per_minute
        self._tokens = float(calls_per_minute)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a token is available, then consume it."""
        async with self._lock:
            self._refill()
            if self._tokens < 1.0:
                wait_time = (1.0 - self._tokens) / self._rate
                await asyncio.sleep(wait_time)
                self._refill()
            self._tokens -= 1.0

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._max_tokens, self._tokens + elapsed * self._rate)
        self._last_refill = now

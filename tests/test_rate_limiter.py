"""Tests for terminalq.rate_limiter — async token bucket."""
import asyncio
import time

import pytest

from terminalq.rate_limiter import RateLimiter


async def test_acquire_under_limit():
    """Acquiring tokens under the burst limit should not block noticeably."""
    limiter = RateLimiter(calls_per_minute=60)
    start = time.monotonic()
    # Should be able to do several calls instantly (burst bucket is full)
    for _ in range(5):
        await limiter.acquire()
    elapsed = time.monotonic() - start
    # 5 calls from a bucket of 60 should be near-instant (< 0.5s)
    assert elapsed < 0.5


async def test_concurrent_access():
    """Multiple concurrent acquire calls should not raise."""
    limiter = RateLimiter(calls_per_minute=120)

    async def _worker():
        await limiter.acquire()
        return True

    results = await asyncio.gather(*[_worker() for _ in range(10)])
    assert all(results)


async def test_token_refill():
    """After draining tokens, refill should allow new acquisitions."""
    # Small bucket so we can drain it quickly
    limiter = RateLimiter(calls_per_minute=6)
    # Drain all 6 tokens
    for _ in range(6):
        await limiter.acquire()

    # At 6 calls/min = 0.1 tokens/sec, we need ~10s for 1 token.
    # Instead of waiting, we manually advance the internal state.
    limiter._last_refill -= 11  # pretend 11 seconds have passed
    limiter._tokens = 0.0  # ensure drained

    # Now refill should give us tokens
    limiter._refill()
    # 11 seconds * 0.1 tokens/sec = 1.1 tokens
    assert limiter._tokens >= 1.0

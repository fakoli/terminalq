"""Finnhub data provider — quotes, company profiles, news, and earnings."""

import asyncio

import httpx

from terminalq import cache
from terminalq.config import (
    CACHE_TTL_CALENDAR,
    CACHE_TTL_EARNINGS,
    CACHE_TTL_FUNDAMENTALS,
    CACHE_TTL_NEWS,
    CACHE_TTL_QUOTES,
    CACHE_TTL_RATINGS,
    FINNHUB_API_KEY,
    FINNHUB_RATE_LIMIT,
)
from terminalq.logging_config import log
from terminalq.rate_limiter import RateLimiter

BASE_URL = "https://finnhub.io/api/v1"
_rate_limiter = RateLimiter(calls_per_minute=FINNHUB_RATE_LIMIT)


def _headers() -> dict:
    return {"X-Finnhub-Token": FINNHUB_API_KEY}


async def _fetch(client: httpx.AsyncClient, url: str, params: dict) -> dict:
    """Rate-limited HTTP GET with error handling."""
    await _rate_limiter.acquire()
    log.debug("Finnhub request: %s params=%s", url, params)
    try:
        resp = await client.get(url, params=params, headers=_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()
    except httpx.TimeoutException:
        log.warning("Finnhub timeout: %s %s", url, params)
        return {"_error": "Request timed out"}
    except httpx.HTTPStatusError as e:
        log.warning("Finnhub HTTP %d: %s %s", e.response.status_code, url, params)
        return {"_error": f"HTTP {e.response.status_code}"}
    except httpx.ConnectError:
        log.error("Finnhub connection failed: %s", url)
        return {"_error": "Connection failed"}


async def get_quote(symbol: str) -> dict:
    """Get real-time quote for a symbol."""
    cache_key = f"finnhub_quote_{symbol}"
    cached = cache.get(cache_key)
    if cached:
        log.debug("Cache hit: %s", cache_key)
        return cached

    async with httpx.AsyncClient() as client:
        data = await _fetch(client, f"{BASE_URL}/quote", {"symbol": symbol})

    if "_error" in data:
        return {"symbol": symbol, "error": data["_error"], "source": "finnhub"}

    result = {
        "symbol": symbol,
        "current_price": data.get("c"),
        "change": data.get("d"),
        "percent_change": data.get("dp"),
        "high": data.get("h"),
        "low": data.get("l"),
        "open": data.get("o"),
        "previous_close": data.get("pc"),
        "timestamp": data.get("t"),
        "source": "finnhub",
    }
    cache.set(cache_key, result, CACHE_TTL_QUOTES)
    return result


async def get_quotes_batch(symbols: list[str]) -> list[dict]:
    """Get quotes for multiple symbols concurrently."""
    results: dict[str, dict] = {}
    uncached: list[str] = []

    # Check cache first
    for symbol in symbols:
        cache_key = f"finnhub_quote_{symbol}"
        cached = cache.get(cache_key)
        if cached:
            log.debug("Cache hit: %s", cache_key)
            results[symbol] = cached
        else:
            uncached.append(symbol)

    if not uncached:
        return [results[s] for s in symbols]

    # Fetch uncached symbols in parallel
    log.info("Fetching %d uncached quotes: %s", len(uncached), uncached)

    async def _fetch_one(client: httpx.AsyncClient, sym: str) -> dict:
        data = await _fetch(client, f"{BASE_URL}/quote", {"symbol": sym})
        if "_error" in data:
            return {"symbol": sym, "error": data["_error"], "source": "finnhub"}
        result = {
            "symbol": sym,
            "current_price": data.get("c"),
            "change": data.get("d"),
            "percent_change": data.get("dp"),
            "high": data.get("h"),
            "low": data.get("l"),
            "open": data.get("o"),
            "previous_close": data.get("pc"),
            "source": "finnhub",
        }
        cache.set(f"finnhub_quote_{sym}", result, CACHE_TTL_QUOTES)
        return result

    async with httpx.AsyncClient() as client:
        tasks = [_fetch_one(client, sym) for sym in uncached]
        fetched = await asyncio.gather(*tasks, return_exceptions=True)

    for sym, result in zip(uncached, fetched):
        if isinstance(result, Exception):
            log.error("Exception fetching %s: %s", sym, result)
            results[sym] = {"symbol": sym, "error": str(result), "source": "finnhub"}
        else:
            results[sym] = result

    return [results[s] for s in symbols if s in results]


async def get_company_profile(symbol: str) -> dict:
    """Get company profile / overview."""
    cache_key = f"finnhub_profile_{symbol}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        data = await _fetch(client, f"{BASE_URL}/stock/profile2", {"symbol": symbol})

    if "_error" in data:
        return {"symbol": symbol, "error": data["_error"], "source": "finnhub"}

    result = {
        "symbol": symbol,
        "name": data.get("name"),
        "exchange": data.get("exchange"),
        "industry": data.get("finnhubIndustry"),
        "market_cap": data.get("marketCapitalization"),
        "shares_outstanding": data.get("shareOutstanding"),
        "logo": data.get("logo"),
        "weburl": data.get("weburl"),
        "ipo": data.get("ipo"),
        "country": data.get("country"),
        "currency": data.get("currency"),
        "source": "finnhub",
    }
    cache.set(cache_key, result, CACHE_TTL_FUNDAMENTALS)
    return result


async def get_company_news(symbol: str, days: int = 7) -> list[dict]:
    """Get recent news for a company."""
    from datetime import datetime, timedelta

    cache_key = f"finnhub_news_{symbol}_{days}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    async with httpx.AsyncClient() as client:
        data = await _fetch(
            client,
            f"{BASE_URL}/company-news",
            {"symbol": symbol, "from": start, "to": end},
        )

    if isinstance(data, dict) and "_error" in data:
        return [{"error": data["_error"], "symbol": symbol, "source": "finnhub"}]

    results = [
        {
            "headline": item.get("headline"),
            "summary": item.get("summary", "")[:200],
            "source": item.get("source"),
            "url": item.get("url"),
            "datetime": item.get("datetime"),
            "category": item.get("category"),
            "related": item.get("related"),
        }
        for item in data[:20]
    ]
    cache.set(cache_key, results, CACHE_TTL_NEWS)
    return results


async def get_earnings(symbol: str) -> dict:
    """Get earnings history and upcoming earnings for a company."""
    cache_key = f"finnhub_earnings_{symbol}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        data = await _fetch(
            client,
            f"{BASE_URL}/stock/earnings",
            {"symbol": symbol, "limit": 8},
        )

    if isinstance(data, dict) and "_error" in data:
        return {"symbol": symbol, "error": data["_error"], "source": "finnhub"}

    earnings = []
    if isinstance(data, list):
        for item in data:
            earnings.append(
                {
                    "period": item.get("period"),
                    "actual_eps": item.get("actual"),
                    "estimate_eps": item.get("estimate"),
                    "surprise": item.get("surprise"),
                    "surprise_percent": item.get("surprisePercent"),
                }
            )

    result = {
        "symbol": symbol,
        "earnings_history": earnings,
        "source": "finnhub",
    }
    cache.set(cache_key, result, CACHE_TTL_EARNINGS)
    return result


async def get_analyst_ratings(symbol: str) -> dict:
    """Get analyst consensus rating and price target for a symbol."""
    cache_key = f"finnhub_ratings_{symbol}"
    cached = cache.get(cache_key)
    if cached:
        log.debug("Cache hit: %s", cache_key)
        return cached

    async with httpx.AsyncClient() as client:
        reco_data, target_data = await asyncio.gather(
            _fetch(client, f"{BASE_URL}/stock/recommendation", {"symbol": symbol}),
            _fetch(client, f"{BASE_URL}/stock/price-target", {"symbol": symbol}),
        )

    # Handle errors
    if isinstance(reco_data, dict) and "_error" in reco_data:
        return {"symbol": symbol, "error": reco_data["_error"], "source": "finnhub"}

    # Parse recommendation trend (most recent first)
    trend = []
    if isinstance(reco_data, list):
        for item in reco_data[:6]:
            trend.append(
                {
                    "period": item.get("period"),
                    "strong_buy": item.get("strongBuy", 0),
                    "buy": item.get("buy", 0),
                    "hold": item.get("hold", 0),
                    "sell": item.get("sell", 0),
                    "strong_sell": item.get("strongSell", 0),
                }
            )

    # Compute consensus from the latest period
    consensus = "N/A"
    total_analysts = 0
    if trend:
        latest = trend[0]
        sb = latest["strong_buy"]
        b = latest["buy"]
        h = latest["hold"]
        s = latest["sell"]
        ss = latest["strong_sell"]
        total_analysts = sb + b + h + s + ss
        if total_analysts > 0:
            score = (sb * 5 + b * 4 + h * 3 + s * 2 + ss * 1) / total_analysts
            if score >= 4.5:
                consensus = "Strong Buy"
            elif score >= 3.5:
                consensus = "Buy"
            elif score >= 2.5:
                consensus = "Hold"
            elif score >= 1.5:
                consensus = "Sell"
            else:
                consensus = "Strong Sell"

    # Parse price target
    price_target = {}
    if isinstance(target_data, dict) and "_error" not in target_data:
        price_target = {
            "target_high": target_data.get("targetHigh"),
            "target_low": target_data.get("targetLow"),
            "target_mean": target_data.get("targetMean"),
            "target_median": target_data.get("targetMedian"),
            "last_updated": target_data.get("lastUpdated"),
        }

    result = {
        "symbol": symbol,
        "consensus": consensus,
        "total_analysts": total_analysts,
        "price_target": price_target,
        "trend": trend,
        "source": "finnhub",
    }
    cache.set(cache_key, result, CACHE_TTL_RATINGS)
    return result


async def get_economic_calendar(days: int = 7) -> dict:
    """Get upcoming economic events calendar.

    Args:
        days: Number of days ahead to fetch (default 7).

    Returns:
        Dict with list of economic events sorted by date, filtered to US.
    """
    from datetime import datetime, timedelta

    cache_key = f"finnhub_econ_calendar_{days}"
    cached = cache.get(cache_key)
    if cached:
        log.debug("Cache hit: %s", cache_key)
        return cached

    start = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    async with httpx.AsyncClient() as client:
        data = await _fetch(
            client,
            f"{BASE_URL}/calendar/economic",
            {"from": start, "to": end},
        )

    if isinstance(data, dict) and "_error" in data:
        return {"error": data["_error"], "source": "finnhub"}

    # Parse events from the response
    raw_events = []
    if isinstance(data, dict):
        raw_events = data.get("economicCalendar", [])

    # Filter to US events and sort by date
    events = []
    for ev in raw_events:
        country = ev.get("country", "")
        if country.upper() not in ("US", "USA", "UNITED STATES"):
            continue

        impact = ev.get("impact", "")
        if isinstance(impact, (int, float)):
            if impact >= 3:
                impact_label = "high"
            elif impact >= 2:
                impact_label = "medium"
            else:
                impact_label = "low"
        else:
            impact_label = str(impact).lower() if impact else "unknown"

        events.append(
            {
                "event": ev.get("event", ""),
                "date": ev.get("time", ev.get("date", "")),
                "impact": impact_label,
                "actual": ev.get("actual"),
                "estimate": ev.get("estimate"),
                "previous": ev.get("prev"),
                "unit": ev.get("unit", ""),
            }
        )

    # Sort by date
    events.sort(key=lambda e: e.get("date", ""))

    # Categorize by impact
    high_impact_count = sum(1 for e in events if e["impact"] == "high")

    result = {
        "period": f"{start} to {end}",
        "total_events": len(events),
        "high_impact_count": high_impact_count,
        "events": events,
        "source": "finnhub",
    }
    cache.set(cache_key, result, CACHE_TTL_CALENDAR)
    return result

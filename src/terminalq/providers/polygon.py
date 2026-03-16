"""Polygon.io fallback provider for historical data and dividends."""

from datetime import datetime, timedelta, timezone

import httpx

from terminalq.config import POLYGON_API_KEY, POLYGON_RATE_LIMIT
from terminalq.logging_config import log
from terminalq.rate_limiter import RateLimiter

BASE_URL = "https://api.polygon.io"
_rate_limiter = RateLimiter(calls_per_minute=POLYGON_RATE_LIMIT)

# Map yfinance period strings to days
_PERIOD_DAYS = {
    "1mo": 30,
    "3mo": 90,
    "6mo": 180,
    "1y": 365,
    "2y": 730,
    "5y": 1825,
    "max": 3650,
}

# Map yfinance interval strings to Polygon multiplier/timespan
_INTERVAL_MAP = {
    "1d": (1, "day"),
    "1wk": (1, "week"),
    "1mo": (1, "month"),
}


async def get_historical(symbol: str, period: str = "1y", interval: str = "1d") -> dict:
    """Fetch historical OHLCV data from Polygon.io.

    Matches the return format of historical.get_historical() for seamless fallback.
    """
    if not POLYGON_API_KEY:
        return {"error": "POLYGON_API_KEY not configured", "symbol": symbol, "source": "polygon.io"}

    days = _PERIOD_DAYS.get(period, 365)
    multiplier, timespan = _INTERVAL_MAP.get(interval, (1, "day"))

    date_to = datetime.now()
    date_from = date_to - timedelta(days=days)

    url = (
        f"{BASE_URL}/v2/aggs/ticker/{symbol}/range"
        f"/{multiplier}/{timespan}"
        f"/{date_from.strftime('%Y-%m-%d')}/{date_to.strftime('%Y-%m-%d')}"
    )

    await _rate_limiter.acquire()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url,
                params={"apiKey": POLYGON_API_KEY, "adjusted": "true", "sort": "asc", "limit": 5000},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        log.warning("Polygon timeout for %s", symbol)
        return {"error": "Request timed out", "symbol": symbol, "source": "polygon.io"}
    except httpx.HTTPStatusError as e:
        log.warning("Polygon HTTP %d for %s", e.response.status_code, symbol)
        return {"error": f"HTTP {e.response.status_code}", "symbol": symbol, "source": "polygon.io"}
    except httpx.ConnectError:
        log.error("Polygon connection failed for %s", symbol)
        return {"error": "Connection failed", "symbol": symbol, "source": "polygon.io"}

    results = data.get("results", [])
    if not results:
        return {"error": "No data from Polygon", "symbol": symbol, "source": "polygon.io"}

    prices = []
    for bar in results:
        prices.append(
            {
                "date": datetime.fromtimestamp(bar["t"] / 1000, tz=timezone.utc).strftime("%Y-%m-%d"),
                "open": round(bar["o"], 2),
                "high": round(bar["h"], 2),
                "low": round(bar["l"], 2),
                "close": round(bar["c"], 2),
                "volume": int(bar["v"]),
            }
        )

    return {
        "symbol": symbol,
        "period": period,
        "interval": interval,
        "data_points": len(prices),
        "prices": prices,
        "source": "polygon.io",
    }


async def get_dividends(symbol: str, years: int = 5) -> dict:
    """Fetch dividend history from Polygon.io.

    Matches the return format of historical.get_dividends() for seamless fallback.
    """
    if not POLYGON_API_KEY:
        return {"error": "POLYGON_API_KEY not configured", "symbol": symbol, "source": "polygon.io"}

    await _rate_limiter.acquire()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/v3/reference/dividends",
                params={
                    "ticker": symbol,
                    "limit": 50,
                    "order": "desc",
                    "sort": "ex_dividend_date",
                    "apiKey": POLYGON_API_KEY,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        log.warning("Polygon dividends timeout for %s", symbol)
        return {"error": "Request timed out", "symbol": symbol, "source": "polygon.io"}
    except httpx.HTTPStatusError as e:
        log.warning("Polygon dividends HTTP %d for %s", e.response.status_code, symbol)
        return {"error": f"HTTP {e.response.status_code}", "symbol": symbol, "source": "polygon.io"}
    except httpx.ConnectError:
        log.error("Polygon dividends connection failed for %s", symbol)
        return {"error": "Connection failed", "symbol": symbol, "source": "polygon.io"}

    raw_divs = data.get("results", [])

    # Filter to last N years
    cutoff = datetime.now() - timedelta(days=years * 365)
    dividends = []
    for d in raw_divs:
        ex_date = d.get("ex_dividend_date", "")
        if ex_date and datetime.strptime(ex_date, "%Y-%m-%d") >= cutoff:
            dividends.append(
                {
                    "date": ex_date,
                    "amount": round(d.get("cash_amount", 0), 4),
                }
            )

    # Sort chronologically
    dividends.sort(key=lambda x: x["date"])

    # Calculate annual dividend from last 4 payments
    recent = dividends[-4:] if len(dividends) >= 4 else dividends
    annual_dividend = round(sum(d["amount"] for d in recent), 4)

    # Determine payout frequency
    payments_per_year = len(dividends) / max(years, 1)
    if payments_per_year >= 11:
        payout_frequency = "monthly"
    elif payments_per_year >= 3.5:
        payout_frequency = "quarterly"
    elif payments_per_year >= 1.5:
        payout_frequency = "semi-annual"
    elif payments_per_year >= 0.5:
        payout_frequency = "annual"
    else:
        payout_frequency = "irregular" if dividends else "none"

    return {
        "symbol": symbol,
        "dividends": dividends,
        "annual_dividend": annual_dividend,
        "dividend_yield": None,  # No price data from this endpoint
        "payout_frequency": payout_frequency,
        "source": "polygon.io",
    }

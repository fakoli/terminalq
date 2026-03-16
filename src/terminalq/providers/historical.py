"""Yahoo Finance historical data provider — price history and dividends.

Uses yfinance as the primary source with Polygon.io as a fallback when
yfinance fails or returns empty data.
"""

import asyncio
from datetime import datetime, timedelta

import yfinance

from terminalq import cache
from terminalq.config import CACHE_TTL_DIVIDENDS, CACHE_TTL_HISTORY, POLYGON_API_KEY
from terminalq.logging_config import log

# ---------------------------------------------------------------------------
# Internal helpers — yfinance fetches
# ---------------------------------------------------------------------------


async def _fetch_yfinance_historical(symbol: str, period: str, interval: str) -> dict:
    """Attempt to fetch historical data from yfinance.

    Returns a result dict on success, or a dict with an ``"error"`` key on
    failure.
    """
    ticker = yfinance.Ticker(symbol)
    df = await asyncio.to_thread(ticker.history, period=period, interval=interval)

    if df.empty:
        return {
            "error": "No historical data available",
            "symbol": symbol,
            "source": "yahoo_finance",
        }

    prices = []
    for idx, row in df.iterrows():
        prices.append(
            {
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            }
        )

    return {
        "symbol": symbol,
        "period": period,
        "interval": interval,
        "data_points": len(prices),
        "prices": prices,
        "source": "yahoo_finance",
    }


async def _fetch_yfinance_dividends(symbol: str, years: int) -> dict:
    """Attempt to fetch dividend data from yfinance.

    Returns a result dict on success, or a dict with an ``"error"`` key on
    failure.
    """
    ticker = yfinance.Ticker(symbol)
    div_series = await asyncio.to_thread(lambda: ticker.dividends)

    if div_series.empty:
        return {
            "symbol": symbol,
            "dividends": [],
            "annual_dividend": 0.0,
            "dividend_yield": None,
            "payout_frequency": "none",
            "source": "yahoo_finance",
        }

    # Filter to last N years
    cutoff = datetime.now() - timedelta(days=years * 365)
    div_series = div_series[div_series.index >= cutoff]

    dividends = [
        {
            "date": idx.strftime("%Y-%m-%d"),
            "amount": round(float(amount), 4),
        }
        for idx, amount in div_series.items()
    ]

    # Calculate annual dividend from the last 4 payments
    recent = div_series.tail(4)
    annual_dividend = round(float(recent.sum()), 4)

    # Determine payout frequency from the number of payments in the most
    # recent full calendar year (or all available data if less).
    payments_per_year = len(div_series) / max(years, 1)
    if payments_per_year >= 11:
        payout_frequency = "monthly"
    elif payments_per_year >= 3.5:
        payout_frequency = "quarterly"
    elif payments_per_year >= 1.5:
        payout_frequency = "semi-annual"
    elif payments_per_year >= 0.5:
        payout_frequency = "annual"
    else:
        payout_frequency = "irregular"

    # Calculate dividend yield using current price
    current_price = None
    dividend_yield = None
    try:
        info = await asyncio.to_thread(lambda: ticker.fast_info)
        current_price = float(info["lastPrice"])
        if current_price > 0:
            dividend_yield = round(annual_dividend / current_price, 4)
    except Exception:
        log.debug("Could not fetch current price for yield calc: %s", symbol)

    return {
        "symbol": symbol,
        "dividends": dividends,
        "annual_dividend": annual_dividend,
        "dividend_yield": dividend_yield,
        "payout_frequency": payout_frequency,
        "source": "yahoo_finance",
    }


# ---------------------------------------------------------------------------
# Public API — with Polygon.io fallback
# ---------------------------------------------------------------------------


async def get_historical(symbol: str, period: str = "1y", interval: str = "1d") -> dict:
    """Get historical price data for a symbol.

    Tries yfinance first; falls back to Polygon.io when yfinance fails or
    returns empty data and ``POLYGON_API_KEY`` is configured.
    """
    cache_key = f"yahoo_history_{symbol}_{period}_{interval}"
    cached = cache.get(cache_key)
    if cached:
        log.debug("Cache hit: %s", cache_key)
        return cached

    # --- Primary: yfinance ---
    yf_error = None
    try:
        result = await _fetch_yfinance_historical(symbol, period, interval)
        if "error" not in result:
            cache.set(cache_key, result, CACHE_TTL_HISTORY)
            return result
        yf_error = result.get("error", "Unknown yfinance error")
        log.warning("yfinance returned error for %s: %s", symbol, yf_error)
    except Exception as e:
        yf_error = str(e)
        log.error("yfinance exception for %s: %s", symbol, e)

    # --- Fallback: Polygon.io ---
    if POLYGON_API_KEY:
        log.info("Falling back to Polygon.io for %s historical data", symbol)
        try:
            from terminalq.providers.polygon import get_historical as polygon_historical

            result = await polygon_historical(symbol, period, interval)
            if "error" not in result:
                result["source"] = "polygon.io (fallback)"
                cache.set(cache_key, result, CACHE_TTL_HISTORY)
                return result
            log.warning("Polygon.io also failed for %s: %s", symbol, result.get("error"))
        except Exception as e:
            log.error("Polygon.io exception for %s: %s", symbol, e)

    # --- Both sources failed ---
    return {
        "error": f"All data sources failed. yfinance: {yf_error}",
        "symbol": symbol,
        "source": "all_failed",
    }


async def get_dividends(symbol: str, years: int = 5) -> dict:
    """Get dividend history and metrics for a symbol.

    Tries yfinance first; falls back to Polygon.io when yfinance fails or
    returns an error and ``POLYGON_API_KEY`` is configured.
    """
    cache_key = f"yahoo_dividends_{symbol}_{years}"
    cached = cache.get(cache_key)
    if cached:
        log.debug("Cache hit: %s", cache_key)
        return cached

    # --- Primary: yfinance ---
    yf_error = None
    try:
        result = await _fetch_yfinance_dividends(symbol, years)
        if "error" not in result:
            cache.set(cache_key, result, CACHE_TTL_DIVIDENDS)
            return result
        yf_error = result.get("error", "Unknown yfinance error")
        log.warning("yfinance dividends returned error for %s: %s", symbol, yf_error)
    except Exception as e:
        yf_error = str(e)
        log.error("yfinance dividends exception for %s: %s", symbol, e)

    # --- Fallback: Polygon.io ---
    if POLYGON_API_KEY:
        log.info("Falling back to Polygon.io for %s dividend data", symbol)
        try:
            from terminalq.providers.polygon import get_dividends as polygon_dividends

            result = await polygon_dividends(symbol, years)
            if "error" not in result:
                result["source"] = "polygon.io (fallback)"
                cache.set(cache_key, result, CACHE_TTL_DIVIDENDS)
                return result
            log.warning("Polygon.io dividends also failed for %s: %s", symbol, result.get("error"))
        except Exception as e:
            log.error("Polygon.io dividends exception for %s: %s", symbol, e)

    # --- Both sources failed ---
    return {
        "error": f"All data sources failed. yfinance: {yf_error}",
        "symbol": symbol,
        "source": "all_failed",
    }

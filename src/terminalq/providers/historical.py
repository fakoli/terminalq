"""Yahoo Finance historical data provider — price history and dividends."""
import asyncio
from datetime import datetime, timedelta

import yfinance

from terminalq import cache
from terminalq.config import CACHE_TTL_HISTORY, CACHE_TTL_DIVIDENDS
from terminalq.logging_config import log


async def get_historical(
    symbol: str, period: str = "1y", interval: str = "1d"
) -> dict:
    """Get historical price data for a symbol."""
    cache_key = f"yahoo_history_{symbol}_{period}_{interval}"
    cached = cache.get(cache_key)
    if cached:
        log.debug("Cache hit: %s", cache_key)
        return cached

    try:
        ticker = yfinance.Ticker(symbol)
        df = await asyncio.to_thread(
            ticker.history, period=period, interval=interval
        )

        if df.empty:
            log.warning("No historical data for %s", symbol)
            return {
                "error": "No historical data available",
                "symbol": symbol,
                "source": "yahoo_finance",
            }

        prices = []
        for idx, row in df.iterrows():
            prices.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })

        result = {
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "data_points": len(prices),
            "prices": prices,
            "source": "yahoo_finance",
        }
        cache.set(cache_key, result, CACHE_TTL_HISTORY)
        return result

    except Exception as e:
        log.error("Error fetching historical data for %s: %s", symbol, e)
        return {"error": str(e), "symbol": symbol, "source": "yahoo_finance"}


async def get_dividends(symbol: str, years: int = 5) -> dict:
    """Get dividend history and metrics for a symbol."""
    cache_key = f"yahoo_dividends_{symbol}_{years}"
    cached = cache.get(cache_key)
    if cached:
        log.debug("Cache hit: %s", cache_key)
        return cached

    try:
        ticker = yfinance.Ticker(symbol)
        div_series = await asyncio.to_thread(lambda: ticker.dividends)

        if div_series.empty:
            log.info("No dividend data for %s", symbol)
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

        result = {
            "symbol": symbol,
            "dividends": dividends,
            "annual_dividend": annual_dividend,
            "dividend_yield": dividend_yield,
            "payout_frequency": payout_frequency,
            "source": "yahoo_finance",
        }
        cache.set(cache_key, result, CACHE_TTL_DIVIDENDS)
        return result

    except Exception as e:
        log.error("Error fetching dividend data for %s: %s", symbol, e)
        return {"error": str(e), "symbol": symbol, "source": "yahoo_finance"}

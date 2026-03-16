"""FRED (Federal Reserve Economic Data) provider — economic indicators and dashboard."""

import asyncio

import httpx

from terminalq import cache
from terminalq.config import CACHE_TTL_ECONOMIC, CACHE_TTL_ECONOMIC_INTRADAY, FRED_API_KEY
from terminalq.logging_config import log

BASE_URL = "https://api.stlouisfed.org/fred"

SERIES_MAP = {
    "gdp": "GDP",
    "real_gdp": "GDPC1",
    "cpi": "CPIAUCSL",
    "core_cpi": "CPILFESL",
    "ppi": "PPIACO",
    "unemployment": "UNRATE",
    "fed_funds": "DFF",
    "10y_yield": "DGS10",
    "2y_yield": "DGS2",
    "30y_yield": "DGS30",
    "yield_spread": "T10Y2Y",
    "initial_claims": "ICSA",
    "nonfarm_payrolls": "PAYEMS",
    "pce": "PCE",
    "housing_starts": "HOUST",
    "consumer_sentiment": "UMCSENT",
}

# Series that update intraday (use shorter cache)
INTRADAY_SERIES = {"DFF", "DGS10", "DGS2", "DGS30", "T10Y2Y"}


def _resolve_series_id(series_id: str) -> str:
    """Resolve a human-friendly alias to a FRED series ID."""
    return SERIES_MAP.get(series_id.lower(), series_id)


async def get_series(series_id: str, limit: int = 12) -> dict:
    """Get observations for a FRED series.

    Args:
        series_id: FRED series ID or alias (e.g. "gdp", "cpi", "DGS10").
        limit: Number of most-recent observations to return.

    Returns:
        Dict with series metadata, latest value, and observations list.
    """
    if not FRED_API_KEY:
        return {
            "error": "FRED_API_KEY not configured. Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html",
            "source": "fred",
        }

    resolved_id = _resolve_series_id(series_id)
    log.info("FRED get_series: series=%s resolved=%s", series_id, resolved_id)
    cache_key = f"fred_{resolved_id}_{limit}"
    cached = cache.get(cache_key)
    if cached:
        log.debug("Cache hit: %s", cache_key)
        return cached

    ttl = CACHE_TTL_ECONOMIC_INTRADAY if resolved_id in INTRADAY_SERIES else CACHE_TTL_ECONOMIC

    try:
        async with httpx.AsyncClient() as client:
            obs_resp, info_resp = await asyncio.gather(
                client.get(
                    f"{BASE_URL}/series/observations",
                    params={
                        "series_id": resolved_id,
                        "api_key": FRED_API_KEY,
                        "file_type": "json",
                        "sort_order": "desc",
                        "limit": limit,
                    },
                    timeout=10,
                ),
                client.get(
                    f"{BASE_URL}/series",
                    params={
                        "series_id": resolved_id,
                        "api_key": FRED_API_KEY,
                        "file_type": "json",
                    },
                    timeout=10,
                ),
            )
            obs_resp.raise_for_status()
            info_resp.raise_for_status()
            obs_data = obs_resp.json()
            info_data = info_resp.json()
    except httpx.TimeoutException:
        log.warning("FRED timeout for series %s", resolved_id)
        return {"error": "Request timed out", "source": "fred"}
    except httpx.HTTPStatusError as e:
        log.warning("FRED HTTP %d for series %s: %s", e.response.status_code, resolved_id, e.response.text[:200])
        return {
            "error": f"HTTP {e.response.status_code}",
            "detail": e.response.text[:300],
            "series": resolved_id,
            "source": "fred",
        }
    except httpx.ConnectError:
        log.error("FRED connection failed for series %s", resolved_id)
        return {"error": "Connection failed", "source": "fred"}

    # Parse series info
    series_info = {}
    serieses = info_data.get("seriess", [])
    if serieses:
        series_info = serieses[0]

    title = series_info.get("title", "")
    frequency = series_info.get("frequency", "")
    units = series_info.get("units", "")

    # Parse observations — skip entries where value is "."
    observations = []
    for obs in obs_data.get("observations", []):
        raw_value = obs.get("value", ".")
        if raw_value == ".":
            continue
        try:
            observations.append(
                {
                    "date": obs["date"],
                    "value": float(raw_value),
                }
            )
        except (ValueError, KeyError):
            continue

    latest_value = observations[0]["value"] if observations else None
    latest_date = observations[0]["date"] if observations else None

    result = {
        "series_id": resolved_id,
        "title": title,
        "frequency": frequency,
        "units": units,
        "latest_value": latest_value,
        "latest_date": latest_date,
        "observations": observations,
        "source": "fred",
    }
    cache.set(cache_key, result, ttl)
    return result


async def get_economic_dashboard() -> dict:
    """Fetch key economic indicators in parallel for a dashboard view.

    Returns:
        Dict with an 'indicators' mapping containing latest/previous values
        and change for each indicator.
    """
    if not FRED_API_KEY:
        return {
            "error": "FRED_API_KEY not configured. Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html",
            "source": "fred",
        }

    cache_key = "fred_dashboard"
    cached = cache.get(cache_key)
    if cached:
        log.debug("Cache hit: %s", cache_key)
        return cached

    dashboard_aliases = [
        "gdp",
        "cpi",
        "core_cpi",
        "unemployment",
        "fed_funds",
        "10y_yield",
        "2y_yield",
        "yield_spread",
        "initial_claims",
        "nonfarm_payrolls",
        "consumer_sentiment",
    ]

    results = await asyncio.gather(
        *[get_series(alias, limit=2) for alias in dashboard_aliases],
        return_exceptions=True,
    )

    indicators = {}
    for alias, result in zip(dashboard_aliases, results):
        if isinstance(result, BaseException):
            log.error("Exception fetching %s: %s", alias, result)
            indicators[alias] = {"error": str(result)}
            continue

        if not isinstance(result, dict) or "error" in result:
            indicators[alias] = {
                "error": result.get("error", "Unknown error") if isinstance(result, dict) else str(result)
            }
            continue

        obs = result.get("observations", [])
        latest_value = obs[0]["value"] if len(obs) > 0 else None
        latest_date = obs[0]["date"] if len(obs) > 0 else None
        previous_value = obs[1]["value"] if len(obs) > 1 else None

        change = None
        if latest_value is not None and previous_value is not None:
            change = round(latest_value - previous_value, 4)

        indicators[alias] = {
            "latest_value": latest_value,
            "latest_date": latest_date,
            "previous_value": previous_value,
            "change": change,
        }

    result = {
        "indicators": indicators,
        "source": "fred",
    }
    # Only cache if at least one indicator succeeded
    has_data = any("latest_value" in v for v in indicators.values() if isinstance(v, dict))
    if has_data:
        cache.set(cache_key, result, CACHE_TTL_ECONOMIC)
    return result


# --- Forex (currency pair) series ---
FOREX_SERIES_MAP = {
    "eurusd": "DEXUSEU",
    "usdjpy": "DEXJPUS",
    "gbpusd": "DEXUSUK",
    "usdchf": "DEXSZUS",
    "usdcad": "DEXCAUS",
    "audusd": "DEXUSAL",
    "nzdusd": "DEXUSNZ",
    "usdcny": "DEXCHUS",
    "usdinr": "DEXINUS",
    "usdmxn": "DEXMXUS",
    "usdbrl": "DEXBZUS",
    "usdkrw": "DEXKOUS",
    "usdsgd": "DEXSIUS",
    "usdhkd": "DEXHKUS",
}


async def get_forex(pair: str, limit: int = 30) -> dict:
    """Get exchange rate data for a currency pair via FRED.

    Args:
        pair: Currency pair alias (e.g. "eurusd", "usdjpy") or FRED series ID.
        limit: Number of most-recent observations to return.

    Returns:
        Dict with latest rate, observations, and change info.
    """
    if not FRED_API_KEY:
        return {
            "error": "FRED_API_KEY not configured. Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html",
            "source": "fred",
        }

    resolved_id = FOREX_SERIES_MAP.get(pair.lower(), pair)
    log.info("FRED get_forex: pair=%s resolved=%s", pair, resolved_id)

    cache_key = f"fred_forex_{resolved_id}_{limit}"
    cached = cache.get(cache_key)
    if cached:
        log.debug("Cache hit: %s", cache_key)
        return cached

    try:
        async with httpx.AsyncClient() as client:
            obs_resp, info_resp = await asyncio.gather(
                client.get(
                    f"{BASE_URL}/series/observations",
                    params={
                        "series_id": resolved_id,
                        "api_key": FRED_API_KEY,
                        "file_type": "json",
                        "sort_order": "desc",
                        "limit": limit,
                    },
                    timeout=10,
                ),
                client.get(
                    f"{BASE_URL}/series",
                    params={
                        "series_id": resolved_id,
                        "api_key": FRED_API_KEY,
                        "file_type": "json",
                    },
                    timeout=10,
                ),
            )
            obs_resp.raise_for_status()
            info_resp.raise_for_status()
            obs_data = obs_resp.json()
            info_data = info_resp.json()
    except httpx.TimeoutException:
        log.warning("FRED timeout for forex %s", resolved_id)
        return {"error": "Request timed out", "source": "fred"}
    except httpx.HTTPStatusError as e:
        log.warning("FRED HTTP %d for forex %s", e.response.status_code, resolved_id)
        return {"error": f"HTTP {e.response.status_code}", "source": "fred"}
    except httpx.ConnectError:
        log.error("FRED connection failed for forex %s", resolved_id)
        return {"error": "Connection failed", "source": "fred"}

    # Parse series info
    series_info = {}
    serieses = info_data.get("seriess", [])
    if serieses:
        series_info = serieses[0]

    title = series_info.get("title", "")
    units = series_info.get("units", "")

    # Parse observations
    observations = []
    for obs in obs_data.get("observations", []):
        raw_value = obs.get("value", ".")
        if raw_value == ".":
            continue
        try:
            observations.append(
                {
                    "date": obs["date"],
                    "value": float(raw_value),
                }
            )
        except (ValueError, KeyError):
            continue

    latest_value = observations[0]["value"] if observations else None
    latest_date = observations[0]["date"] if observations else None
    previous_value = observations[1]["value"] if len(observations) > 1 else None

    change = None
    change_pct = None
    if latest_value is not None and previous_value is not None:
        change = round(latest_value - previous_value, 6)
        if previous_value != 0:
            change_pct = round((change / previous_value) * 100, 4)

    result = {
        "pair": pair.upper(),
        "series_id": resolved_id,
        "title": title,
        "units": units,
        "latest_rate": latest_value,
        "latest_date": latest_date,
        "previous_rate": previous_value,
        "change": change,
        "change_pct": change_pct,
        "observations": observations,
        "source": "fred",
    }
    cache.set(cache_key, result, CACHE_TTL_ECONOMIC_INTRADAY)
    return result
